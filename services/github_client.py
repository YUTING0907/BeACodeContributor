# services/github_client.py
import requests
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class GitHubIssue:
    """GitHub Issue数据模型"""
    id: int
    number: int
    title: str
    body: str
    state: str
    labels: List[str]
    created_at: datetime
    updated_at: datetime
    html_url: str
    comments: int
    reactions: Dict[str, int]
    assignee: Optional[str]
    milestone: Optional[str]

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'GitHubIssue':
        return cls(
            id=data['id'],
            number=data['number'],
            title=data['title'],
            body=data['body'] or '',
            state=data['state'],
            labels=[label['name'] for label in data['labels']],
            created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00')),
            html_url=data['html_url'],
            comments=data['comments'],
            reactions=data.get('reactions', {}),
            assignee=data['assignee']['login'] if data['assignee'] else None,
            milestone=data['milestone']['title'] if data['milestone'] else None
        )


class GitHubClient:
    """GitHub API客户端"""

    def __init__(self, token: str = None):
        self.token = token or settings.GITHUB_TOKEN
        self.base_url = settings.GITHUB_API_URL
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'BigData-Contributor-AI'
        }

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """发送HTTP请求"""
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                timeout=30,
                **kwargs
            )
            response.raise_for_status()

            # GitHub API速率限制检查
            if 'X-RateLimit-Remaining' in response.headers:
                remaining = int(response.headers['X-RateLimit-Remaining'])
                if remaining < 10:
                    logger.warning(f"GitHub API rate limit remaining: {remaining}")

            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"GitHub API请求失败: {e}")
            raise

    def get_repository_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """获取仓库信息"""
        return self._make_request('GET', f'repos/{owner}/{repo}')

    def get_issues(self, owner: str, repo: str, state: str = 'open',
                   labels: List[str] = None, per_page: int = 100) -> List[GitHubIssue]:
        """获取Issue列表"""
        params = {
            'state': state,
            'per_page': per_page,
            'page': 1
        }

        if labels:
            params['labels'] = ','.join(labels)

        issues = []
        while True:
            try:
                data = self._make_request('GET', f'repos/{owner}/{repo}/issues', params=params)
                if not data:
                    break

                for issue_data in data:
                    # 过滤掉Pull Request
                    if 'pull_request' not in issue_data:
                        response = GitHubIssue.from_api_response(issue_data)
                        issues.append(response)

                # 检查是否有更多页面
                if len(data) < per_page:
                    break

                params['page'] += 1
                time.sleep(0.5)  # 避免速率限制

            except Exception as e:
                logger.error(f"获取Issue失败: {e}")
                break

        return issues

    def get_issue_details(self, owner: str, repo: str, issue_number: int) -> Dict[str, Any]:
        """获取Issue详情"""
        return self._make_request('GET', f'repos/{owner}/{repo}/issues/{issue_number}')

    def get_issue_comments(self, owner: str, repo: str, issue_number: int) -> List[Dict[str, Any]]:
        """获取Issue评论"""
        return self._make_request('GET', f'repos/{owner}/{repo}/issues/{issue_number}/comments')

    def get_readme(self, owner: str, repo: str) -> str:
        """获取README内容"""
        try:
            data = self._make_request('GET', f'repos/{owner}/{repo}/readme')
            import base64
            content = base64.b64decode(data['content']).decode('utf-8')
            return content
        except:
            return ""

    def get_contributing_guide(self, owner: str, repo: str) -> str:
        """获取CONTRIBUTING指南"""
        try:
            data = self._make_request('GET', f'repos/{owner}/{repo}/contents/CONTRIBUTING.md')
            import base64
            content = base64.b64decode(data['content']).decode('utf-8')
            return content
        except:
            return ""

    def get_code_of_conduct(self, owner: str, repo: str) -> str:
        """获取行为准则"""
        try:
            data = self._make_request('GET', f'repos/{owner}/{repo}/contents/CODE_OF_CONDUCT.md')
            import base64
            content = base64.b64decode(data['content']).decode('utf-8')
            return content
        except:
            return ""

    def get_project_files(self, owner: str, repo: str, path: str = "") -> List[str]:
        """获取项目文件列表"""
        try:
            data = self._make_request('GET', f'repos/{owner}/{repo}/contents/{path}')
            return [item['name'] for item in data if item['type'] == 'file']
        except:
            return []

    def search_repositories(self, query: str, language: str = None,
                            stars: str = ">100", per_page: int = 30) -> List[Dict[str, Any]]:
        """搜索仓库"""
        search_query = f"{query} stars:{stars}"
        if language:
            search_query += f" language:{language}"

        params = {
            'q': search_query,
            'sort': 'stars',
            'order': 'desc',
            'per_page': per_page
        }

        data = self._make_request('GET', 'search/repositories', params=params)
        return data.get('items', [])