# services/feishu_client.py
import requests
import json
import time
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
from config.settings import settings

logger = logging.getLogger(__name__)


class FeishuCardBuilder:
    """飞书卡片消息构建器"""

    @staticmethod
    def build_issue_card(issue: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """构建Issue推送卡片"""

        # 难度颜色映射
        difficulty_colors = {
            "beginner": "green",
            "intermediate": "orange",
            "advanced": "red"
        }

        color = difficulty_colors.get(analysis.get('difficulty_level', 'intermediate'), "blue")

        card = {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"🚀 大数据Issue推荐: {issue.get('title', '')[:50]}"
                },
                "template": color
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**项目**: {issue.get('repo', '')}\n"
                                   f"**Issue**: #{issue.get('number')} - [{issue.get('title', '')}]({issue.get('html_url')})"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**难度**: {analysis.get('difficulty_level', '未知')}"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**预计时间**: {analysis.get('estimated_time', '未知')}"
                            }
                        },
                        {
                            "is_short": False,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**所需技能**: {', '.join(analysis.get('required_skills', []))}"
                            }
                        }
                    ]
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**解决方案思路**:\n{analysis.get('solution_approach', '暂无')}"
                    }
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**学习机会**:\n{chr(10).join(analysis.get('learning_opportunities', []))}"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "查看Issue详情"
                            },
                            "type": "primary",
                            "url": issue.get('html_url', '')
                        },
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "开始贡献"
                            },
                            "type": "default",
                            "url": issue.get('html_url', '') + "#issuecomment"
                        }
                    ]
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        }
                    ]
                }
            ]
        }

        return card

    @staticmethod
    def build_daily_summary(projects: List[Dict[str, Any]],
                            issues_found: int,
                            recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """构建每日摘要卡片（包含技术细节）"""

        project_list = "\n".join([f"• {p.get('name')} ({p.get('owner')}/{p.get('repo')})"
                                  for p in projects])

        # 1. 构建推荐 Issue 详情列表
        elements = [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**监控项目**:\n{project_list}\n\n"
                               f"**发现Issue总数**: {issues_found} | **推荐Issue数**: {len(recommendations)}"
                }
            },
            {"tag": "hr"}
        ]

        # 2. 遍历推荐内容，添加详细的技术说明
        for i, rec in enumerate(recommendations[:5]):  # 限制前3个，防止卡片过长
            # 格式化技能要求
            skills = "、".join(rec.get("required_skills", []))

            item_md = (
                f"**{i + 1}. [{rec.get('title')}]({rec.get('url')})**\n"
                f"🔸 **难度**: {rec.get('difficulty', '未知')} | ⏳ **预计耗时**: {rec.get('estimated_time', 'N/A')}\n"
                f"🎯 **所需技能**: {skills}\n"
                f"💡 **解决方案**: {rec.get('solution_approach', '暂无建议')}\n"
                f"🛠 **技术拆解**: {rec.get('technical_breakdown', '暂无拆解')}"
            )

            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": item_md
                }
            })
            # 如果不是最后一个，添加分割线
            if i < len(recommendations[:3]) - 1:
                elements.append({"tag": "hr"})

        # 3. 添加底部信息
        elements.extend([
            {"tag": "hr"},
            {
                "tag": "note",
                "elements": [
                    {
                        "tag": "plain_text",
                        "content": f"报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            }
        ])

        card = {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "📊 大数据项目贡献每日摘要"
                },
                "template": "blue"
            },
            "elements": elements
        }

        return card

class FeishuClient:
    """飞书客户端"""

    def __init__(self, webhook_url: str = None,
                 app_id: str = None,
                 app_secret: str = None,
                 user_id: str = None):
        self.webhook_url = webhook_url or settings.FEISHU_WEBHOOK_URL
        self.app_id = app_id or settings.FEISHU_APP_ID
        self.app_secret = app_secret or settings.FEISHU_APP_SECRET
        self.user_id = user_id or settings.FEISHU_USER_ID
        self.access_token = None
        self.token_expire_time = 0

    def _get_access_token(self) -> Optional[str]:
        """获取访问令牌"""
        if self.access_token and time.time() < self.token_expire_time:
            return self.access_token

        if not self.app_id or not self.app_secret:
            return None

        try:
            url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
            headers = {
                "Content-Type": "application/json"
            }
            data = {
                "app_id": self.app_id,
                "app_secret": self.app_secret
            }

            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()

            result = response.json()
            if result.get("code") == 0:
                self.access_token = result.get("tenant_access_token")
                self.token_expire_time = time.time() + result.get("expire", 3600) - 300
                return self.access_token

        except Exception as e:
            logger.error(f"获取飞书访问令牌失败: {e}")

        return None

    def send_webhook_message(self, card_content: Dict[str, Any]) -> bool:
        """通过Webhook发送消息"""
        try:
            data = {
                "msg_type": "interactive",
                "card": card_content
            }

            response = requests.post(
                self.webhook_url,
                headers={"Content-Type": "application/json"},
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    logger.info("飞书消息发送成功")
                    return True
                else:
                    logger.error(f"飞书消息发送失败: {result}")
            else:
                logger.error(f"飞书请求失败: {response.status_code}")

        except Exception as e:
            logger.error(f"发送飞书消息失败: {e}")

        return False

    def send_api_message(self, receive_id: str,
                         msg_type: str,
                         content: Dict[str, Any],
                         receive_id_type: str = "open_id") -> bool:  # 建议默认 open_id
        token = self._get_access_token()
        if not token:
            return False

        try:
            url = "https://open.feishu.cn/open-apis/im/v1/messages"
            # 建议通过前缀自动判断，或者外部显式指定
            if receive_id.startswith("ou_"):
                receive_id_type = "open_id"
            elif receive_id.startswith("oc_"):
                receive_id_type = "chat_id"

            params = {"receive_id_type": receive_id_type}
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=utf-8"
            }

            data = {
                "receive_id": receive_id,
                "msg_type": msg_type,
                "content": json.dumps(content, ensure_ascii=False)
            }

            response = requests.post(url, params=params, headers=headers, json=data, timeout=30)

            # 核心调试步骤：如果失败，打印出飞书给出的具体报错原因
            if response.status_code != 200:
                logger.error(f"飞书请求失败，状态码: {response.status_code}, 原因: {response.text}")
                return False

            result = response.json()
            if result.get("code") == 0:
                logger.info("飞书API消息发送成功")
                return True
            else:
                logger.error(f"业务发送失败，错误码: {result.get('code')}, 消息: {result.get('msg')}")

        except Exception as e:
            logger.error(f"调用飞书接口发生异常: {e}")

        return False

    def send_issue_recommendation(self, issue: Dict[str, Any],
                                  analysis: Dict[str, Any]) -> bool:
        """发送Issue推荐"""
        card = FeishuCardBuilder.build_issue_card(issue, analysis)
        return self.send_webhook_message(card)

    def send_daily_summary(self, projects: List[Dict[str, Any]],
                           issues_found: int,
                           recommendations: List[Dict[str, Any]]) -> bool:
        """发送每日摘要"""
        card = FeishuCardBuilder.build_daily_summary(projects, issues_found, recommendations)
        print(card)

        return self.send_api_message(self.user_id, "interactive", card)

    def send_contribution_plan(self, user_id: str,
                               issue: Dict[str, Any],
                               plan: Dict[str, Any]) -> bool:
        """发送个性化贡献计划"""
        card = {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "📝 个性化贡献计划"
                },
                "template": "purple"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**Issue**: [{issue.get('title', '')}]({issue.get('html_url')})\n"
                                   f"**生成时间**: {plan.get('generated_at', '')}"
                    }
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": plan.get('plan', '')
                    }
                }
            ]
        }

        return self.send_api_message(user_id, "interactive", card)
if __name__ == "__main__":

    feishu_client = FeishuClient()
    projects = [{
        'name': "druid",
        'owner': "druid",
        'repo': "druid"
    }]

    recommendations = [{
        'title':  "Missing Native Query documentation for Window Functions",
        'url': "https://github.com/apache/druid/issues/18872",
        'difficulty': "beginner"
    }]

    feishu_client.send_daily_summary(
        projects, 1, recommendations
    )