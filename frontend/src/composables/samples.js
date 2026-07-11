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
}
