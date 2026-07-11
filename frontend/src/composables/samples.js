/**
 * 每个 QC 工具的示例数据 —— 打开工具页 → 一键填入 → 立即看到成品
 * 每个工具至少 1 组示例, 覆盖典型制造业场景
 */
export const SAMPLES = {

  relations: [
    { id: 'welding', name: '焊接不良率上升', data: {
      topic: '焊接不良率上升',
      context: '3号焊接线不良率从1.2%升至3.5%，客户投诉激增',
      raw_causes: `焊工技能不齐
参数漂移
熔深不足
送丝机抖动
流量表偏差
焊枪磨损
保护气纯度不足
焊丝公差偏大
新人培训缺失
巡检频率不足`,
    }},
    { id: 'complaint', name: '客户投诉响应慢', data: {
      topic: '客户投诉响应慢',
      context: '首次响应时间从2小时延长至8小时',
      raw_causes: `客服人员不足
工单系统卡顿
夜班无人值守
分派规则复杂
知识库过时`,
    }},
  ],

  affinity: [
    { id: 'complaint', name: '客户投诉分类', data: {
      topic: '客户投诉分类',
      context: '近30天收到的客户投诉汇总',
      raw_items: `前台冷淡
不主动询问
打断客户
语气生硬
首响>10分
转接多次
邮件未回
工单积压
外包装破损
内衬缺失
同款贵5%
无促销
物流慢
APP闪退`,
    }},
  ],

  pareto: [
    { id: 'defects', name: '产线不良分布', data: {
      topic: '产线不良分布',
      metric: '频次',
      threshold: 80,
      raw_data: `焊接,142
装配,118
喷涂,52
包装,36
检验,28
运输,12
其他,12`,
    }},
  ],

  radar: [
    { id: 'supplier', name: '供应商综合评分', data: {
      topic: '供应商综合评分',
      subject: '供应商A',
      dimensions: [
        { name: '质量', value: 8.5, target: 9 },
        { name: '交期', value: 7.2, target: 8.5 },
        { name: '价格', value: 8.8, target: 8 },
        { name: '服务', value: 7.6, target: 8 },
        { name: '技术', value: 6.5, target: 7.5 },
        { name: '配合度', value: 8.0, target: 8 },
      ],
    }},
  ],

  w5h2: [
    { id: 'defect', name: '降低焊接不良率', data: {
      topic: '降低焊接不良率',
      context: '3号线不良率3.5%，客户要求降至1.5%以下',
    }},
  ],

  rca: [
    { id: 'welding', name: '焊接不良根因', data: {
      topic: '焊接不良率上升',
      problem: '3号线焊接不良率从1.2%升至3.5%，客户投诉',
      end_causes_text: `熔深不足
电流参数偏低
新人自行调低电流
培训体系未涵盖参数权限`,
    }},
  ],

  fishbone: [
    { id: 'dimension', name: '产品尺寸超差', data: {
      topic: '产品尺寸超差',
      statement: '关键尺寸 Cpk < 1.0',
      layers: 2,
      categories: [
        { name: '人', children: [
          { name: '技能不足' }, { name: '注意力涣散' }, { name: '轮岗频繁' },
        ]},
        { name: '机', children: [
          { name: '主轴磨损' }, { name: '刀具跳动' }, { name: '夹具松动' },
        ]},
        { name: '料', children: [
          { name: '来料公差偏' }, { name: '硬度不均' },
        ]},
        { name: '法', children: [
          { name: '工艺参数不合理' }, { name: '首件检验缺失' },
        ]},
      ],
    }},
  ],

  qcc_guide: [
    { id: 'defect', name: '降低生产不良率', data: {
      topic: '降低3号焊接线不良率',
      context: '当前不良率3.5%，目标降至1.2%以下',
      team_size: 6,
    }},
  ],

  tree: [
    { id: 'defect', name: '降低3号线不良率', data: {
      topic: '3 个月内将 3 号焊接线不良率从 3.5% 降至 1.2% 以下',
      context: '客户投诉激增，QCC 项目立项',
      layers: 3,
      hints: ['焊工技能', '设备状态', 'SOP 更新'],
    }},
  ],

  matrix: [
    { id: 'qfd', name: 'QFD 客户需求×工程特性', data: {
      topic: '产品客户需求 vs 工程特性',
      row_label: '客户需求',
      col_label: '工程特性',
      rows_text: '外观美观\n操作简单\n坚固耐用\n价格实惠\n售后便利',
      cols_text: '表面工艺\n按钮布局\n材料强度\n制造成本\n服务网点数',
      context: '面向 25-40 岁家庭用户的中端产品',
    }},
  ],

  mda: [
    { id: 'supplier', name: '供应商 5 家综合评估', data: {
      topic: '5 家供应商综合评估',
      metrics_text: '质量,交期,价格,服务,技术',
      lower_is_better_text: '交期,价格',
      subjects_text: `供应商A,9,7,8,9,8
供应商B,8,9,7,7,9
供应商C,6,6,5,6,5
供应商D,7,8,9,7,7
供应商E,5,5,6,5,4`,
    }},
  ],

  pdpc: [
    { id: 'launch', name: '12 月新产品量产上线', data: {
      topic: '12 月新产品量产上线',
      steps_text: '物料到位\n试产验证\n量产切换\n首批交付',
      risk_dims_text: '供应,技术,质量,进度',
      context: '关键料交期紧张，工艺参数尚未完全定型',
    }},
  ],

  arrow: [
    { id: 'qcc12w', name: 'QCC 项目 12 周计划', data: {
      topic: 'QCC 项目 12 周排期',
      tasks_text: `选题,3,,张三
现状调查,7,选题,李四
目标设定,2,选题,张三
要因分析,8,现状调查,王五
对策制定,5,要因分析,团队
实施,12,对策制定,王五
效果确认,5,实施,李四
标准化,3,效果确认,张三`,
      auto_infer: true,
    }},
  ],
}
