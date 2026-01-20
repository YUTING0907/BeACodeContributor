# services/ai_analyzer.py
import openai
import json
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from dataclasses import dataclass
from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class IssueAnalysis:
    """Issue分析结果"""
    issue_id: int
    complexity_score: float  # 0-1，越高越复杂
    difficulty_level: str  # beginner/intermediate/advanced
    required_skills: List[str]
    estimated_time: str  # 预计解决时间
    solution_approach: str  # 解决方案思路
    technical_breakdown: Dict[str, Any]
    learning_opportunities: List[str]
    confidence_score: float


@dataclass
class ProjectAnalysis:
    """项目分析结果"""
    project_name: str
    beginner_friendliness: float
    active_maintenance: bool
    community_health: Dict[str, Any]
    contribution_guidelines: Dict[str, Any]
    tech_stack_analysis: Dict[str, Any]
    recommended_issues: List[int]


class AIAnalyzer:
    """AI分析引擎"""

    def __init__(self, api_key: str = None):
        self.client = openai.OpenAI(
            api_key=api_key or settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )

    def analyze_issue(self, issue: Dict[str, Any],
                      readme_content: str = "",
                      contributing_guide: str = "") -> IssueAnalysis:
        """分析单个Issue的技术需求和解决方案"""

        prompt = self._build_issue_analysis_prompt(issue, readme_content, contributing_guide)

        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": """你是一个大数据开源项目专家，专门帮助开发者分析GitHub Issue。
                        你需要准确评估Issue的技术复杂度、所需技能、解决方案和预计时间。"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )

            analysis_text = response.choices[0].message.content
            analysis_data = self._parse_analysis_response(analysis_text)

            return IssueAnalysis(
                issue_id=issue['id'],
                complexity_score=analysis_data.get('complexity_score', 0.5),
                difficulty_level=analysis_data.get('difficulty_level', 'intermediate'),
                required_skills=analysis_data.get('required_skills', []),
                estimated_time=analysis_data.get('estimated_time', '未知'),
                solution_approach=analysis_data.get('solution_approach', ''),
                technical_breakdown=analysis_data.get('technical_breakdown', {}),
                learning_opportunities=analysis_data.get('learning_opportunities', []),
                confidence_score=analysis_data.get('confidence_score', 0.8)
            )

        except Exception as e:
            logger.error(f"AI分析失败: {e}")
            # 返回默认分析结果
            return self._get_default_analysis(issue)

    def analyze_project(self, project_data: Dict[str, Any],
                        issues: List[Dict[str, Any]]) -> ProjectAnalysis:
        """分析整个项目的贡献友好度"""

        prompt = self._build_project_analysis_prompt(project_data, issues)

        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": """你是一个开源社区专家，专门评估项目的贡献者友好度。
                        分析项目的社区健康度、维护活跃度、新手友好度等指标。"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=1500
            )

            analysis_text = response.choices[0].message.content
            analysis_data = self._parse_project_analysis_response(analysis_text)

            return ProjectAnalysis(
                project_name=project_data.get('name', ''),
                beginner_friendliness=analysis_data.get('beginner_friendliness', 0.5),
                active_maintenance=analysis_data.get('active_maintenance', False),
                community_health=analysis_data.get('community_health', {}),
                contribution_guidelines=analysis_data.get('contribution_guidelines', {}),
                tech_stack_analysis=analysis_data.get('tech_stack_analysis', {}),
                recommended_issues=analysis_data.get('recommended_issues', [])
            )

        except Exception as e:
            logger.error(f"项目分析失败: {e}")
            return self._get_default_project_analysis(project_data)

    def generate_contribution_plan(self, issue: Dict[str, Any],
                                   analysis: IssueAnalysis,
                                   user_skills: List[str]) -> Dict[str, Any]:
        """生成个性化的贡献计划"""

        prompt = f"""
        基于以下信息，为开发者生成详细的贡献计划：

        Issue信息：
        - 标题：{issue.get('title')}
        - 描述：{issue.get('body', '')[:500]}...

        AI分析结果：
        - 难度级别：{analysis.difficulty_level}
        - 所需技能：{', '.join(analysis.required_skills)}
        - 解决方案思路：{analysis.solution_approach[:200]}...

        开发者技能：
        {', '.join(user_skills)}

        请生成包含以下内容的贡献计划：
        1. 学习路径建议
        2. 代码阅读指南
        3. 具体实现步骤
        4. 测试建议
        5. 提交PR的注意事项
        6. 预计时间线
        """

        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "你是开源贡献导师，为开发者提供个性化的贡献指导。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1500
            )

            plan_text = response.choices[0].message.content
            return {
                "plan": plan_text,
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"生成贡献计划失败: {e}")
            return {"plan": "无法生成贡献计划", "generated_at": datetime.now().isoformat()}

    def _build_issue_analysis_prompt(self, issue: Dict[str, Any],
                                     readme: str, contributing: str) -> str:
        """构建Issue分析提示词"""

        prompt = f"""
        请分析以下GitHub Issue，评估技术复杂度和贡献可行性：

        Issue标题：{issue.get('title')}
        Issue描述：{issue.get('body', '无描述')[:1000]}
        标签：{', '.join(issue.get('labels', []))}
        创建时间：{issue.get('created_at')}
        评论数量：{issue.get('comments', 0)}

        项目README摘要（前500字）：
        {readme[:500]}

        贡献指南摘要（如有）：
        {contributing[:500] if contributing else '无贡献指南'}

        请以JSON格式返回分析结果，包含以下字段：
        1. complexity_score: 复杂度评分（0-1）
        2. difficulty_level: 难度等级（beginner/intermediate/advanced）
        3. required_skills: 所需技能列表
        4. estimated_time: 预计解决时间（如：2-4小时，1-2天等）
        5. solution_approach: 解决方案思路（200字以内）
        6. technical_breakdown: 技术分解（如：需要修改哪些文件，使用什么技术）
        7. learning_opportunities: 学习机会（从此Issue中可以学到什么）
        8. confidence_score: 分析置信度（0-1）

        特别注意：
        1. 如果Issue属于大数据项目（Spark、Flink、Kafka等），请考虑分布式系统特性
        2. 评估是否需要深入理解项目架构
        3. 考虑测试和文档的要求
        """

        return prompt

    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """解析AI分析响应"""
        try:
            # 尝试提取JSON部分
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_match = re.search(r'({.*})', response_text, re.DOTALL)
                json_str = json_match.group(1) if json_match else response_text

            return json.loads(json_str)
        except:
            # 如果无法解析JSON，返回默认值
            return {
                "complexity_score": 0.5,
                "difficulty_level": "intermediate",
                "required_skills": [],
                "estimated_time": "未知",
                "solution_approach": "",
                "technical_breakdown": {},
                "learning_opportunities": [],
                "confidence_score": 0.5
            }

    def _get_default_analysis(self, issue: Dict[str, Any]) -> IssueAnalysis:
        """获取默认的Issue分析"""
        return IssueAnalysis(
            issue_id=issue['id'],
            complexity_score=0.5,
            difficulty_level='intermediate',
            required_skills=['Git', '项目相关语言'],
            estimated_time='1-3天',
            solution_approach='需要先理解项目架构和代码组织',
            technical_breakdown={},
            learning_opportunities=['学习项目代码结构', '理解分布式系统概念'],
            confidence_score=0.5
        )