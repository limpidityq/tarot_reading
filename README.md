# 韦特塔罗 · Tarot Reading（重构版）

基于原有 Streamlit + DeepSeek 的个人塔罗工具，新增：

1. **78 张 Rider–Waite–Smith 牌面**：1／2／3 张抽牌，抽牌不重复；逆位牌面倒转。
2. **Waite 原著释义**：每张牌均有正、逆位的英文原文，并可查看小阿卡纳附加释义。来源是 A. E. Waite 的 *The Pictorial Key to the Tarot*（1911），避免混用现代牌义。没有统一且持续更新的“韦特官方解读”版本；这里采用作者本人发表的历史原文。
3. **历史记录**：在同一个浏览器中自动保存抽牌时间、问题（可空）、牌名与正逆位；支持搜索、逐条删除、全部清空和导出 JSON。**不会保存 AI 回答、API Key**。
4. **独立牌库**：不抽牌也可以逐张浏览 78 张牌和原著释义。
5. **保留 DeepSeek**：输入自己的 API Key 后，按需生成基于原著释义的**中文**综合解读。无需 Key 也能抽牌、看原文和保存历史。

## 与原仓库的关系

本文件包基于原仓库 `limpidityq/tarot_reading`，替换根目录 `app.py`、`requirements.txt`，新增 `tarot_core.py`、`history.js`、`scripts/` 和 `tests/`。原仓库 `data/` 内的五组旧版现代关键词 JSON、CSV、XLSX 和 `tarot.py` 可以保留作备份，重构应用不再读取它们。

## 快速开始

使用 Python 3.10+：

```bash
pip install -r requirements.txt
# 建议只运行一次，将准确的 Waite 牌义缓存为本地 data/cards_waite.json
python scripts/build_waite_data.py
streamlit run app.py
```

`data/cards_waite.json` 已存在时，程序优先读本地快照；若不存在，首次运行会从固定版本的开放数据仓库下载并保存到当前运行目录。**首次下载需要网络**；如果运行环境无法访问 GitHub，请先在能联网的电脑运行构建脚本，然后将生成的 `data/cards_waite.json` 一并上传到仓库。图片为第三方托管地址，显示时也需要网络。

## 部署和升级

如果你原先使用 Streamlit Community Cloud，继续使用现有部署、入口 `app.py` 即可；把本文件包合并至自己的 GitHub 仓库后，平台会重新构建依赖。`streamlit>=1.52` 是为了使用 `st.html(..., unsafe_allow_javascript=True)` 在浏览器保存历史；无需数据库或另接第三方服务。

**历史限制**：历史存放在 `localStorage`，按网站域名和浏览器区分。它不能自动跨设备同步；浏览器清理网站数据、隐身模式退出后可能丢失。建议定期点击「导出 JSON」备份。浏览器禁用本地存储时，历史会报错，抽牌与牌义仍可使用。问题不会写入 GitHub 或托管服务器文件，但生成 AI 解读时，问题和牌面会发送给 DeepSeek API。

## 数据和出处

- **牌义原著**：A. E. Waite，*The Pictorial Key to the Tarot*（1911），[Wikisource 原文](https://en.wikisource.org/wiki/The_Pictorial_Key_to_the_Tarot)。历史用语会与现代塔罗入门教材有明显差异。
- **结构化文字来源**：[StarTarotOnline/tarot-rws-dataset](https://github.com/StarTarotOnline/tarot-rws-dataset)，版本固定到 `7f8ab42b62eef5d018536b8775010e3d6e61eb27`，整理数据采用 **CC BY 4.0**，请保留出处和许可标注；[项目许可](https://github.com/StarTarotOnline/tarot-rws-dataset/blob/main/LICENSE)。
- **牌面来源**：[sixseeds/tarot-api](https://github.com/sixseeds/tarot-api)，原绘为 Pamela Colman Smith（1909），卡牌图像托管于 `petaloverflow.github.io`。原版图像在美国属公有领域；其他地区及后期印刷版本需依当地法律核对。

## 代码检查

```bash
python -m unittest discover -s tests
node --check history.js  # 电脑上有 Node.js 才需要执行
```

本项目仅作象征解读和个人反思工具，牌面结果不能用来验证或保证现实事件的结果。
