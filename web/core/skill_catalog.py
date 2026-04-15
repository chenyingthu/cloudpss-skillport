"""
Skill catalog: dynamic discovery from cloudpss-toolkit registry.

Wraps the toolkit's auto_discover() and list_skills() to provide
a cached, portal-friendly skill listing.
"""
from typing import Dict, Any, List, Optional
from functools import lru_cache


@lru_cache(maxsize=1)
def _discover():
    """Auto-discover all skills and cache the result.

    Note: Importing cloudpss_skills.builtin triggers auto-registration
    via module-level side effects in each skill file.
    """
    import cloudpss_skills.builtin  # noqa: F401 — triggers registration
    from cloudpss_skills import list_skills
    return list_skills()


def list_all() -> List[Any]:
    """Return list of all registered skill instances."""
    return _discover()


def get_skill(name: str) -> Optional[Any]:
    """Get a skill instance by name."""
    from cloudpss_skills import get_skill as toolkit_get_skill
    _discover()
    try:
        return toolkit_get_skill(name)
    except Exception:
        return None


def get_config_schema(name: str) -> Optional[Dict[str, Any]]:
    """Get the JSON schema for a skill's config."""
    skill = get_skill(name)
    if skill is None:
        return None
    return getattr(skill, "config_schema", {})


def get_skill_info(name: str) -> Dict[str, str]:
    """Get human-readable skill info for UI display."""
    skill = get_skill(name)
    if skill is None:
        return {"name": name, "description": "Unknown skill", "version": "?"}
    return {
        "name": getattr(skill, "name", name),
        "description": getattr(skill, "description", ""),
        "version": getattr(skill, "version", "1.0.0"),
    }


# Skill category mapping for UI grouping
CATEGORIES = {
    "仿真执行": ["power_flow", "emt_simulation", "emt_fault_study", "short_circuit"],
    "N-1/N-2安全": ["n1_security", "n2_security", "emt_n1_screening", "contingency_analysis", "maintenance_security"],
    "批量与扫描": ["batch_powerflow", "param_scan", "fault_clearing_scan", "fault_severity_scan", "batch_task_manager", "config_batch_runner", "orthogonal_sensitivity"],
    "稳定性分析": ["voltage_stability", "transient_stability", "transient_stability_margin", "small_signal_stability", "frequency_response", "vsi_weak_bus", "dudv_curve"],
    "结果处理": ["result_compare", "visualize", "waveform_export", "hdf5_export", "disturbance_severity", "compare_visualization", "comtrade_export"],
    "电能质量": ["harmonic_analysis", "power_quality_analysis", "reactive_compensation_design"],
    "新能源": ["renewable_integration"],
    "模型与拓扑": ["topology_check", "parameter_sensitivity", "auto_channel_setup", "auto_loop_breaker", "model_parameter_extractor", "model_builder", "model_validator", "component_catalog", "thevenin_equivalent", "model_hub"],
    "分析报告": ["loss_analysis", "protection_coordination", "report_generator"],
    "流程编排": ["study_pipeline"],
}


# GitLab docs URL base — change if repository path changes
DOCS_BASE_URL = "https://git.tsinghua.edu.cn/chen_ying/cloudpss-toolkit/-/blob/main/docs/skills/"

# Doc file mapping: skill_name → markdown filename (defaults to skill_name + .md)
SKILL_DOCS = {
    "power_flow": "power_flow.md",
    "emt_simulation": "emt_simulation.md",
    "emt_fault_study": "emt_fault_study.md",
    "short_circuit": "short_circuit.md",
    "n1_security": "n1_security.md",
    "n2_security": "n2_security.md",
    "emt_n1_screening": "emt_n1_screening.md",
    "contingency_analysis": "contingency_analysis.md",
    "maintenance_security": "maintenance_security.md",
    "batch_powerflow": "batch_powerflow.md",
    "param_scan": "param_scan.md",
    "fault_clearing_scan": "fault_clearing_scan.md",
    "fault_severity_scan": "fault_severity_scan.md",
    "batch_task_manager": "batch_task_manager.md",
    "config_batch_runner": "config_batch_runner.md",
    "orthogonal_sensitivity": "orthogonal_sensitivity.md",
    "voltage_stability": "voltage_stability.md",
    "transient_stability": "transient_stability.md",
    "transient_stability_margin": "transient_stability_margin.md",
    "small_signal_stability": "small_signal_stability.md",
    "frequency_response": "frequency_response.md",
    "vsi_weak_bus": "vsi_weak_bus.md",
    "dudv_curve": "dudv_curve.md",
    "result_compare": "result_compare.md",
    "visualize": "visualize.md",
    "waveform_export": "waveform_export.md",
    "hdf5_export": "hdf5_export.md",
    "disturbance_severity": "disturbance_severity.md",
    "compare_visualization": "compare_visualization.md",
    "comtrade_export": "comtrade_export.md",
    "harmonic_analysis": "harmonic_analysis.md",
    "power_quality_analysis": "power_quality_analysis.md",
    "reactive_compensation_design": "reactive_compensation_design.md",
    "renewable_integration": "renewable_integration.md",
    "topology_check": "topology_check.md",
    "parameter_sensitivity": "parameter_sensitivity.md",
    "auto_channel_setup": "auto_channel_setup.md",
    "auto_loop_breaker": "auto_loop_breaker.md",
    "model_parameter_extractor": "model_parameter_extractor.md",
    "model_builder": "model_builder.md",
    "model_validator": "model_validator.md",
    "component_catalog": "component_catalog.md",
    "thevenin_equivalent": "thevenin_equivalent.md",
    "model_hub": "model_hub.md",
    "loss_analysis": "loss_analysis.md",
    "protection_coordination": "protection_coordination.md",
    "report_generator": "report_generator.md",
    "study_pipeline": "study_pipeline.md",
}


def get_skill_doc_url(name: str) -> str:
    """Get the GitLab documentation URL for a skill."""
    doc_file = SKILL_DOCS.get(name, f"{name}.md")
    return f"{DOCS_BASE_URL}{doc_file}"


# Quick help descriptions: concise usage guidance per skill
QUICK_HELP = {
    "power_flow": {
        "features": ["牛顿-拉夫逊法 / 快速解耦法", "自动收敛控制", "完整结果输出（母线电压、支路潮流、网损）"],
        "use_cases": ["稳态潮流分析", "网损计算", "电压分布检查"],
        "example": "帮我跑个IEEE39潮流计算，收敛精度1e-8",
    },
    "emt_simulation": {
        "features": ["电磁暂态仿真", "波形数据导出", "故障事件注入"],
        "use_cases": ["暂态过程分析", "故障波形查看", "保护动作验证"],
        "example": "对IEEE3做EMT仿真5秒钟，积分步长50us",
    },
    "emt_fault_study": {
        "features": ["多故障类型研究", "自动扫描故障位置", "波形对比分析"],
        "use_cases": ["故障类型研究", "最严重故障定位", "保护配合验证"],
        "example": "对IEEE3做单相接地故障研究，故障位置从10%到90%",
    },
    "short_circuit": {
        "features": ["短路电流计算", "多故障类型支持", "短路容量分析"],
        "use_cases": ["设备选型校验", "短路容量评估", "保护定值整定"],
        "example": "计算IEEE39各母线三相短路电流",
    },
    "n1_security": {
        "features": ["N-1预想事故扫描", "电压越限检查", "热稳定校验"],
        "use_cases": ["安全校核", "薄弱环节识别", "检修方案评估"],
        "example": "对IEEE39做N-1安全校核，检查电压和热稳定",
    },
    "n2_security": {
        "features": ["N-2双重故障扫描", "级联故障分析", "严重度评估"],
        "use_cases": ["极端工况校核", "电网韧性评估"],
        "example": "对IEEE39做N-2安全分析",
    },
    "emt_n1_screening": {
        "features": ["基于EMT的N-1筛查", "暂态过程分析", "波形级验证"],
        "use_cases": ["精确N-1验证", "EMT级安全筛查"],
        "example": "用EMT方法对IEEE3做N-1安全筛查",
    },
    "contingency_analysis": {
        "features": ["预想事故分析", "自动排序", "越限统计"],
        "use_cases": ["事故预案制定", "关键故障识别"],
        "example": "对IEEE39做预想事故分析，列出前10个最严重事故",
    },
    "maintenance_security": {
        "features": ["检修方式校核", "多设备停运分析", "安全裕度评估"],
        "use_cases": ["检修计划安全评估", "备用容量校验"],
        "example": "校核线路L1+L2同时检修时的安全性",
    },
    "batch_powerflow": {
        "features": ["批量潮流计算", "多场景分析", "结果汇总"],
        "use_cases": ["多运行方式对比", "年度方式计算"],
        "example": "对5个不同场景分别做潮流计算",
    },
    "param_scan": {
        "features": ["参数扫描", "自动遍历参数空间", "结果对比"],
        "use_cases": ["参数灵敏度分析", "最优参数搜索"],
        "example": "扫描发电机出力从80%到120%，步长5%",
    },
    "fault_clearing_scan": {
        "features": ["故障清除时间扫描", "CCT计算", "稳定性评估"],
        "use_cases": ["保护动作时间校核", "暂态稳定极限分析"],
        "example": "扫描故障清除时间0.1s到0.5s，评估暂态稳定",
    },
    "fault_severity_scan": {
        "features": ["故障严重度扫描", "多位置分析", "严重程度排序"],
        "use_cases": ["最严重故障点定位", "薄弱区域识别"],
        "example": "扫描线路不同位置的故障严重度",
    },
    "batch_task_manager": {
        "features": ["批量任务管理", "并发控制", "进度跟踪"],
        "use_cases": ["大规模仿真任务管理", "并行计算"],
        "example": "批量提交20个仿真任务，最大并行度4",
    },
    "config_batch_runner": {
        "features": ["多配置批量运行", "自动结果收集", "失败重试"],
        "use_cases": ["多方案对比", "参数优化"],
        "example": "用5个不同的配置文件批量运行潮流计算",
    },
    "orthogonal_sensitivity": {
        "features": ["正交试验设计", "多因素灵敏度分析", "极差分析"],
        "use_cases": ["多参数优化", "关键因素筛选"],
        "example": "用正交表做3因素4水平的灵敏度分析",
    },
    "voltage_stability": {
        "features": ["电压稳定分析", "PV曲线生成", "电压稳定裕度"],
        "use_cases": ["电压稳定评估", "薄弱环节识别"],
        "example": "分析IEEE39的电压稳定性，生成PV曲线",
    },
    "transient_stability": {
        "features": ["暂态稳定分析", "故障后摇摆曲线", "稳定判定"],
        "use_cases": ["暂态稳定评估", "临界切除时间计算"],
        "example": "分析线路三相故障后的暂态稳定性",
    },
    "transient_stability_margin": {
        "features": ["稳定裕度计算", "CCT搜索", "二分法求解"],
        "use_cases": ["稳定极限分析", "保护定值校核"],
        "example": "计算故障的临界切除时间(CCT)",
    },
    "small_signal_stability": {
        "features": ["小信号稳定分析", "特征值计算", "振荡模式识别"],
        "use_cases": ["低频振荡分析", "阻尼比评估"],
        "example": "分析系统的小干扰稳定特征值",
    },
    "frequency_response": {
        "features": ["频率响应分析", "频率变化率计算", "最低频率点"],
        "use_cases": ["频率稳定评估", "一次调频能力验证"],
        "example": "分析发电机跳闸后的频率响应",
    },
    "vsi_weak_bus": {
        "features": ["VSI弱母线分析", "电压稳定指数", "弱母线排序"],
        "use_cases": ["薄弱母线识别", "无功补偿位置选择"],
        "example": "分析IEEE39的VSI，找出最弱的5条母线",
    },
    "dudv_curve": {
        "features": ["DUDV曲线生成", "电压变化率分析", "灵敏度曲线"],
        "use_cases": ["电压稳定性可视化", "灵敏度分析"],
        "example": "生成关键母线的DUDV曲线",
    },
    "result_compare": {
        "features": ["多场景结果对比", "差异分析", "对比表格"],
        "use_cases": ["方案对比", "仿真结果校验"],
        "example": "对比两个潮流计算结果的差异",
    },
    "visualize": {
        "features": ["结果可视化", "单线图展示", "潮流分布图"],
        "use_cases": ["潮流结果查看", "电压分布展示"],
        "example": "可视化潮流计算结果",
    },
    "waveform_export": {
        "features": ["波形数据导出", "CSV/Excel格式", "多通道选择"],
        "use_cases": ["波形数据分析", "外部工具处理"],
        "example": "导出EMT仿真中Bus1的三相电压波形为CSV",
    },
    "hdf5_export": {
        "features": ["HDF5格式导出", "大数据集支持", "压缩存储"],
        "use_cases": ["大规模数据存储", "长期归档"],
        "example": "将仿真结果导出为HDF5格式",
    },
    "disturbance_severity": {
        "features": ["扰动严重度分析", "多指标评估", "排名统计"],
        "use_cases": ["扰动影响评估", "最严重扰动识别"],
        "example": "分析各种扰动的严重度并排序",
    },
    "compare_visualization": {
        "features": ["对比可视化", "多场景叠加", "差异高亮"],
        "use_cases": ["多方案对比展示", "差异分析"],
        "example": "对比可视化两个不同场景的结果",
    },
    "comtrade_export": {
        "features": ["COMTRADE格式导出", "标准格式支持", "多通道"],
        "use_cases": ["保护装置测试", "录波数据生成"],
        "example": "将EMT仿真结果导出为COMTRADE格式",
    },
    "harmonic_analysis": {
        "features": ["谐波分析", "THD计算", "谐波潮流"],
        "use_cases": ["电能质量评估", "谐波源影响分析"],
        "example": "分析系统的谐波含量，计算各母线THD",
    },
    "power_quality_analysis": {
        "features": ["电能质量分析", "电压偏差", "三相不平衡"],
        "use_cases": ["电能质量评估", "标准合规检查"],
        "example": "分析系统的电能质量指标",
    },
    "reactive_compensation_design": {
        "features": ["无功补偿设计", "补偿容量计算", "位置优化"],
        "use_cases": ["无功优化", "电压改善"],
        "example": "为弱母线设计无功补偿方案",
    },
    "renewable_integration": {
        "features": ["新能源接入分析", "SCR计算", "LVRT合规检查"],
        "use_cases": ["新能源并网评估", "并网标准合规"],
        "example": "分析风电接入对系统稳定性的影响",
    },
    "topology_check": {
        "features": ["拓扑检查", "孤岛检测", "连通性分析"],
        "use_cases": ["模型验证", "接线错误排查"],
        "example": "检查IEEE39模型的拓扑连通性",
    },
    "parameter_sensitivity": {
        "features": ["参数灵敏度分析", "灵敏度矩阵", "关键参数识别"],
        "use_cases": ["参数优化", "模型校准"],
        "example": "分析线路参数对潮流结果的灵敏度",
    },
    "auto_channel_setup": {
        "features": ["自动量测配置", "批量添加通道", "智能推荐"],
        "use_cases": ["EMT通道快速配置", "批量量测添加"],
        "example": "自动配置所有母线的电压输出通道",
    },
    "auto_loop_breaker": {
        "features": ["模型自动解环", "控制环路消除", "环路检测"],
        "use_cases": ["控制环路处理", "模型修正"],
        "example": "自动检测并解开模型中的控制环路",
    },
    "model_parameter_extractor": {
        "features": ["模型参数提取", "元件参数查看", "参数导出"],
        "use_cases": ["参数查看", "模型审计"],
        "example": "提取IEEE39中所有发电机的参数",
    },
    "model_builder": {
        "features": ["模型构建/修改", "添加/删除元件", "参数修改"],
        "use_cases": ["模型编辑", "方案修改"],
        "example": "在IEEE39中添加一台发电机",
    },
    "model_validator": {
        "features": ["模型验证", "多相验证", "拓扑/潮流/EMT检查"],
        "use_cases": ["模型质量检查", "新模型验证"],
        "example": "对新导入的IEEE39模型进行全面验证",
    },
    "component_catalog": {
        "features": ["元件目录浏览", "组件类型查询", "参数查看"],
        "use_cases": ["元件查询", "参数参考"],
        "example": "查询模型中所有Load类型的元件",
    },
    "thevenin_equivalent": {
        "features": ["戴维南等值", "PCC点等值阻抗", "短路容量计算"],
        "use_cases": ["系统强度评估", "并网分析"],
        "example": "计算PCC点的戴维南等值阻抗和短路容量",
    },
    "model_hub": {
        "features": ["算例中心管理", "多服务器模型", "跨服务器克隆"],
        "use_cases": ["模型管理", "跨服务器同步"],
        "example": "浏览算例中心中的所有可用模型",
    },
    "loss_analysis": {
        "features": ["网损分析", "支路损耗计算", "降损优化建议"],
        "use_cases": ["网损评估", "降损方案制定"],
        "example": "分析IEEE39的网损分布，找出损耗最大的5条支路",
    },
    "protection_coordination": {
        "features": ["保护整定计算", "保护配合校验", "定值管理"],
        "use_cases": ["保护定值整定", "配合关系校核"],
        "example": "计算线路过流保护的整定值并校验配合关系",
    },
    "report_generator": {
        "features": ["智能报告生成", "DOCX/PDF/Markdown格式", "多技能结果汇总"],
        "use_cases": ["仿真报告生成", "结果汇总"],
        "example": "根据潮流和N-1结果生成一份完整的仿真报告",
    },
    "study_pipeline": {
        "features": ["多技能流程编排", "并行执行", "条件分支", "foreach循环"],
        "use_cases": ["多步骤仿真流程", "自动化分析"],
        "example": "创建流水线：潮流计算 → N-1校核 → 结果可视化",
    },
}


def get_categorized_skills() -> Dict[str, List[Dict[str, str]]]:
    """Return skills grouped by category for the skill picker UI."""
    result = {}
    for category, skill_names in CATEGORIES.items():
        skills_in_cat = []
        for name in skill_names:
            skill = get_skill(name)
            if skill is not None:
                skills_in_cat.append({
                    "name": name,
                    "description": getattr(skill, "description", ""),
                })
        if skills_in_cat:
            result[category] = skills_in_cat
    return result


def get_quick_help(name: str) -> Dict[str, Any]:
    """Get quick help info for a skill (features, use cases, example prompt)."""
    default = {
        "features": [],
        "use_cases": [],
        "example": "",
    }
    return QUICK_HELP.get(name, default)
