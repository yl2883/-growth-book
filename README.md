# 《借你十年成长文字的光》电子书网站

纯静态电子书站点，可直接用 GitHub Pages 部署。

## 本地预览

用浏览器打开 `index.html`，或在项目根目录启动本地服务：

```bash
python3 -m http.server 8080
```

然后访问 <http://localhost:8080>。

## 功能

- 封面进入，向下滚动后封面缩小并浮现题词
- 根据书稿目录自动生成左侧目录（手机端为抽屉）
- 目录搜索、夜间模式、字体大小、阅读进度
- 上一篇 / 下一篇，以及回到上次阅读位置

## 目录结构

```text
index.html
css/style.css
js/app.js
js/book-data.js
images/cover.jpg
scripts/build_book.py
README.md
```

## 更新正文

替换 Word 书稿路径后，在项目根目录执行：

```bash
python3 scripts/build_book.py
```

会重新生成 `js/book-data.js`。

## GitHub Pages

仓库 Settings → Pages → Build and deployment：

- Source: Deploy from a branch
- Branch: `main` / `/ (root)`

保存后，网站地址为：

`https://yl2883.github.io/-growth-book/`
