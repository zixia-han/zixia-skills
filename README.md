# 子夏 Skills

这里存放可公开安装的“子夏”系列 Codex Skills。

## 子夏八字

`zixia-bazi` 自带离线历法引擎，可计算四柱、藏干、十神、大运和流年，并提供结构化八字解读与交界时辰双盘校验。

### 安装

复制下面的命令即可安装：

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo zixia-han/zixia-skills \
  --path zixia-bazi
```

安装后，在新的 Codex 对话中提供阳历出生日期、时间、性别和出生地，并要求使用“子夏八字”即可。

## 说明

- 排盘脚本在本地运行，不需要用户另外安装排盘软件。
- 八字解读属于传统文化参考，不替代医疗、法律、财务或其他专业意见。
- 出生时间接近时辰交界时，应比较两套候选盘；出生证明或可靠记录优先于描述匹配。
