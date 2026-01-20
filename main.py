# main.py
import asyncio
import json
import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from contextlib import asynccontextmanager

from config.settings import settings
from services.github_client import GitHubClient
from services.ai_analyzer import AIAnalyzer
from services.feishu_client import FeishuClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局服务实例
github_client = None
ai_analyzer = None
feishu_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global github_client, ai_analyzer, feishu_client

    # 启动时初始化
    logger.info("初始化服务...")

    try:
        github_client = GitHubClient()
        ai_analyzer = AIAnalyzer()
        feishu_client = FeishuClient()

        # 验证配置
        settings.validate()

        logger.info("服务初始化完成")
        yield

    except Exception as e:
        logger.error(f"服务初始化失败: {e}")
        raise
    finally:
        # 关闭时清理
        logger.info("服务关闭中...")


# 创建FastAPI应用
app = FastAPI(title="大数据贡献者AI助手", lifespan=lifespan)


# 数据模型
class IssueRequest(BaseModel):
    owner: str
    repo: str
    issue_number: int
    user_skills: List[str] = []


class ProjectRequest(BaseModel):
    owner: str
    repo: str
    send_notification: bool = True


class SearchRequest(BaseModel):
    keywords: List[str]
    experience_level: str = "beginner"
    max_issues: int = 10


@app.get("/")
async def root():
    return {"message": "大数据贡献者AI助手服务运行中", "status": "healthy"}


@app.post("/api/analyze-issue")
async def analyze_issue(request: IssueRequest):
    """分析单个Issue"""
    try:
        # 获取Issue信息
        issue_data = github_client.get_issue_details(
            request.owner, request.repo, request.issue_number
        )

        # 获取项目文档
        readme = github_client.get_readme(request.owner, request.repo)
        contributing = github_client.get_contributing_guide(request.owner, request.repo)

        # AI分析
        analysis = ai_analyzer.analyze_issue(issue_data, readme, contributing)

        # 如果需要，生成贡献计划
        contribution_plan = None
        if request.user_skills:
            contribution_plan = ai_analyzer.generate_contribution_plan(
                issue_data, analysis, request.user_skills
            )

        # 推送飞书通知
        if feishu_client:
            issue_info = {
                'repo': f"{request.owner}/{request.repo}",
                'number': issue_data.get('number'),
                'title': issue_data.get('title'),
                'html_url': issue_data.get('html_url')
            }

            analysis_info = {
                'difficulty_level': analysis.difficulty_level,
                'estimated_time': analysis.estimated_time,
                'required_skills': analysis.required_skills,
                'solution_approach': analysis.solution_approach,
                'learning_opportunities': analysis.learning_opportunities
            }

            feishu_client.send_issue_recommendation(issue_info, analysis_info)

        return {
            "issue": issue_data,
            "analysis": analysis.__dict__,
            "contribution_plan": contribution_plan,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"分析Issue失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/find-beginner-issues")
async def find_beginner_issues(request: ProjectRequest):
    """查找适合新手的Issue"""
    try:
        # 获取项目信息
        project_info = github_client.get_repository_info(request.owner, request.repo)

        # 获取所有open的Issue
        issues = github_client.get_issues(
            request.owner, request.repo,
            state='open',
            labels=['good-first-issue', 'beginner-friendly', 'help-wanted']
        )

        if not issues:
            # 如果没有特定标签，获取所有Issue并过滤
            issues = github_client.get_issues(request.owner, request.repo, state='open')

        # 获取项目文档
        readme = github_client.get_readme(request.owner, request.repo)
        contributing = github_client.get_contributing_guide(request.owner, request.repo)

        # 分析每个Issue
        analyzed_issues = []
        for issue in issues[:5]:  # 限制分析数量
            try:
                issue_dict = {
                    'id': issue.id,
                    'number': issue.number,
                    'title': issue.title,
                    'body': issue.body,
                    'labels': issue.labels,
                    'created_at': issue.created_at.isoformat(),
                    'html_url': issue.html_url,
                    'comments': issue.comments
                }

                analysis = ai_analyzer.analyze_issue(issue_dict, readme, contributing)

                if analysis.difficulty_level in ['beginner', 'intermediate']:
                    analyzed_issues.append({
                        'issue': issue_dict,
                        'analysis': analysis.__dict__
                    })

            except Exception as e:
                logger.warning(f"分析Issue #{issue.number}失败: {e}")
                continue

        # 按复杂度排序（从简单到复杂）
        analyzed_issues.sort(key=lambda x: x['analysis']['complexity_score'])

        # 发送摘要通知
        if request.send_notification and feishu_client and analyzed_issues:
            projects = [{
                'name': project_info.get('name'),
                'owner': request.owner,
                'repo': request.repo
            }]

            recommendations = []
            for item in analyzed_issues[:5]:
                issue = item['issue']
                analysis = item['analysis']
                recommendations.append({
                    'title': issue['title'],
                    'url': issue['html_url'],
                    'difficulty': analysis['difficulty_level'],
                    'estimated_time': analysis['estimated_time'],
                    'required_skills': analysis['required_skills'],

                    'solution_approach': analysis['solution_approach'],
                    'technical_breakdown': analysis['technical_breakdown']
                })

            feishu_client.send_daily_summary(
                projects, len(issues), recommendations
            )

        return {
            "project": project_info.get('name'),
            "total_issues_found": len(issues),
            "recommended_issues": len(analyzed_issues),
            "issues": analyzed_issues[:10],  # 返回前10个
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"查找新手Issue失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search-bigdata-projects")
async def search_bigdata_projects(request: SearchRequest):
    """搜索大数据项目"""
    try:
        projects_config = settings.load_projects_config()
        bigdata_projects = projects_config.get('bigdata_projects', [])

        # 根据关键词过滤项目
        filtered_projects = []
        for project in bigdata_projects:
            # 检查是否匹配关键词
            matches_keyword = any(
                keyword.lower() in project['name'].lower() or
                keyword.lower() in project['category'].lower()
                for keyword in request.keywords
            ) if request.keywords else True

            # 检查经验级别匹配
            matches_experience = (
                    (request.experience_level == 'beginner' and project.get('beginner_friendly', False)) or
                    (request.experience_level == 'intermediate') or
                    (request.experience_level == 'advanced' and not project.get('beginner_friendly', True))
            )

            if matches_keyword and matches_experience:
                filtered_projects.append(project)

        # 获取每个项目的Issue信息
        results = []
        for project in filtered_projects[:5]:  # 限制数量
            try:
                # 获取仓库信息
                repo_info = github_client.get_repository_info(project['owner'], project['name'])

                # 获取新手Issue
                issues = github_client.get_issues(
                    project['owner'], project['name'],
                    labels=project.get('good_first_issue_labels', ['good-first-issue'])
                )

                # AI分析项目
                analysis = ai_analyzer.analyze_project(repo_info, [
                    {
                        'id': issue.id,
                        'title': issue.title,
                        'body': issue.body,
                        'labels': issue.labels,
                        'comments': issue.comments
                    }
                    for issue in issues[:5]
                ])

                results.append({
                    'project': project,
                    'repo_info': {
                        'stars': repo_info.get('stargazers_count', 0),
                        'forks': repo_info.get('forks_count', 0),
                        'open_issues': repo_info.get('open_issues_count', 0),
                        'last_updated': repo_info.get('updated_at')
                    },
                    'analysis': analysis.__dict__,
                    'beginner_issues_count': len(issues)
                })

                # 避免API速率限制
                await asyncio.sleep(1)

            except Exception as e:
                logger.warning(f"获取项目 {project['owner']}/{project['name']} 失败: {e}")
                continue

        return {
            "total_projects_found": len(filtered_projects),
            "analyzed_projects": len(results),
            "projects": results,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"搜索大数据项目失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/daily-monitor")
async def daily_monitor():
    """每日监控任务"""
    try:
        projects_config = settings.load_projects_config()
        bigdata_projects = projects_config.get('bigdata_projects', [])

        all_recommendations = []
        total_issues = 0

        for project in bigdata_projects[:10]:  # 每天监控10个项目
            try:
                # 获取新手Issue
                issues = github_client.get_issues(
                    project['owner'], project['name'],
                    labels=project.get('good_first_issue_labels', ['good-first-issue']),
                    state='open'
                )

                total_issues += len(issues)

                if issues:
                    # 获取README用于分析
                    readme = github_client.get_readme(project['owner'], project['name'])

                    # 分析每个Issue
                    for issue in issues[:3]:  # 每个项目分析前3个
                        try:
                            issue_dict = {
                                'id': issue.id,
                                'number': issue.number,
                                'title': issue.title,
                                'body': issue.body,
                                'labels': issue.labels,
                                'html_url': issue.html_url
                            }

                            analysis = ai_analyzer.analyze_issue(issue_dict, readme, "")

                            if analysis.difficulty_level in ['beginner', 'intermediate']:
                                all_recommendations.append({
                                    'project': f"{project['owner']}/{project['name']}",
                                    'title': issue.title,
                                    'url': issue.html_url,
                                    'difficulty': analysis.difficulty_level,
                                    'analysis': analysis.__dict__
                                })

                        except Exception as e:
                            logger.warning(f"分析Issue失败: {e}")
                            continue

                await asyncio.sleep(2)  # 避免速率限制

            except Exception as e:
                logger.warning(f"监控项目 {project['name']} 失败: {e}")
                continue

        # 发送每日摘要
        if feishu_client and all_recommendations:
            feishu_client.send_daily_summary(
                bigdata_projects[:10],
                total_issues,
                all_recommendations[:5]  # 只发送前5个推荐
            )

        return {
            "monitored_projects": len(bigdata_projects[:10]),
            "total_issues_found": total_issues,
            "recommendations_found": len(all_recommendations),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"每日监控失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.MCP_PORT,
        log_level="info"
    )