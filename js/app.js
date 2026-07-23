(() => {
  const BOOK = window.BOOK_DATA;
  if (!BOOK || !BOOK.pages?.length) {
    console.error("BOOK_DATA missing");
    return;
  }

  const STORAGE = {
    theme: "growth-book-theme",
    size: "growth-book-font",
    page: "growth-book-page",
    scroll: "growth-book-scroll",
    entered: "growth-book-entered",
  };

  const pages = BOOK.pages;
  const pageIndex = Object.fromEntries(pages.map((p, i) => [p.id, i]));

  const els = {
    cover: document.getElementById("cover"),
    coverInner: document.getElementById("coverInner"),
    quoteStage: document.getElementById("quoteStage"),
    quoteText: document.getElementById("quoteText"),
    scrollHint: document.getElementById("scrollHint"),
    startRead: document.getElementById("startRead"),
    openTocFromCover: document.getElementById("openTocFromCover"),
    enterBook: document.getElementById("enterBook"),
    resumeHint: document.getElementById("resumeHint"),
    coverAuthor: document.getElementById("coverAuthor"),
    reader: document.getElementById("reader"),
    sidebar: document.getElementById("sidebar"),
    backdrop: document.getElementById("backdrop"),
    toc: document.getElementById("toc"),
    searchInput: document.getElementById("searchInput"),
    menuBtn: document.getElementById("menuBtn"),
    closeSidebar: document.getElementById("closeSidebar"),
    partLabel: document.getElementById("partLabel"),
    pageLabel: document.getElementById("pageLabel"),
    pageContent: document.getElementById("pageContent"),
    page: document.getElementById("page"),
    prevBtn: document.getElementById("prevBtn"),
    nextBtn: document.getElementById("nextBtn"),
    prevTitle: document.getElementById("prevTitle"),
    nextTitle: document.getElementById("nextTitle"),
    tocJump: document.getElementById("tocJump"),
    backCover: document.getElementById("backCover"),
    fontDown: document.getElementById("fontDown"),
    fontUp: document.getElementById("fontUp"),
    themeBtn: document.getElementById("themeBtn"),
    progress: document.getElementById("progress"),
    toast: document.getElementById("toast"),
  };

  let currentId = pages[0].id;
  let coverLocked = false;
  let toastTimer = 0;

  /* ---------- helpers ---------- */
  function notify(text) {
    els.toast.textContent = text;
    els.toast.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => els.toast.classList.remove("show"), 1600);
  }

  function clamp(n, min, max) {
    return Math.max(min, Math.min(max, n));
  }

  /* ---------- theme / font ---------- */
  function applyTheme(theme) {
    document.body.classList.toggle("dark", theme === "dark");
    els.themeBtn.textContent = theme === "dark" ? "☀" : "☾";
    localStorage.setItem(STORAGE.theme, theme);
  }

  function applyFont(size) {
    document.documentElement.style.setProperty("--font-size", `${size}px`);
    localStorage.setItem(STORAGE.size, String(size));
  }

  applyTheme(localStorage.getItem(STORAGE.theme) || "light");
  applyFont(Number(localStorage.getItem(STORAGE.size) || 18));

  els.themeBtn.addEventListener("click", () => {
    applyTheme(document.body.classList.contains("dark") ? "light" : "dark");
  });
  els.fontDown.addEventListener("click", () => {
    applyFont(clamp(Number(localStorage.getItem(STORAGE.size) || 18) - 1, 15, 24));
  });
  els.fontUp.addEventListener("click", () => {
    applyFont(clamp(Number(localStorage.getItem(STORAGE.size) || 18) + 1, 15, 24));
  });

  /* ---------- cover content ---------- */
  if (BOOK.author) els.coverAuthor.textContent = BOOK.author;
  if (BOOK.quoteLines?.length) {
    els.quoteText.innerHTML = BOOK.quoteLines.map((line) => `<span>${line}</span>`).join("");
  }

  const lastId = localStorage.getItem(STORAGE.page);
  const lastPage = lastId && pageIndex[lastId] != null ? pages[pageIndex[lastId]] : null;
  if (lastPage) {
    els.resumeHint.hidden = false;
    els.resumeHint.innerHTML = `上次读到：<a href="#" id="resumeLink">${lastPage.title}</a>`;
    document.getElementById("resumeLink").addEventListener("click", (e) => {
      e.preventDefault();
      enterReader(lastPage.id, true);
    });
  }

  /* ---------- cover scroll interaction ---------- */
  function updateCoverByScroll() {
    if (coverLocked || document.body.classList.contains("cover-done")) return;

    const viewH = window.innerHeight || 1;
    const maxScroll = Math.max(els.cover.offsetHeight - viewH, 1);
    const p = clamp(window.scrollY / maxScroll, 0, 1);

    const scale = 1 - p * 0.38;
    const opacity = 1 - Math.max(0, p - 0.15) / 0.55;
    els.coverInner.style.transform = `scale(${scale}) translateY(${p * -28}px)`;
    els.coverInner.style.opacity = String(clamp(opacity, 0, 1));

    const quoteOn = p > 0.38;
    els.quoteStage.classList.toggle("visible", quoteOn);
    els.quoteStage.setAttribute("aria-hidden", quoteOn ? "false" : "true");
    els.scrollHint.style.opacity = p > 0.12 ? "0" : "0.85";
  }

  window.addEventListener("scroll", updateCoverByScroll, { passive: true });
  updateCoverByScroll();

  /* ---------- TOC ---------- */
  function buildToc() {
    const frag = document.createDocumentFragment();
    BOOK.toc.forEach((item) => {
      const a = document.createElement("a");
      a.href = `#${item.pageId || item.id}`;
      a.textContent = item.title;
      a.dataset.pageId = item.pageId || "";
      a.dataset.kind = item.kind || "";
      a.dataset.title = item.title;
      a.className = `toc-l${item.level || 3}`;
      a.addEventListener("click", (e) => {
        e.preventDefault();
        if (!item.pageId) return;
        openPage(item.pageId);
        closeSidebar();
      });
      frag.appendChild(a);
    });
    els.toc.innerHTML = "";
    els.toc.appendChild(frag);
  }

  buildToc();

  function setActiveToc(pageId) {
    els.toc.querySelectorAll("a").forEach((a) => {
      a.classList.toggle("active", a.dataset.pageId === pageId);
    });
    const active = els.toc.querySelector("a.active");
    if (active && els.sidebar.classList.contains("open") === false) {
      // keep visible in desktop sidebar
      const side = els.sidebar;
      const top = active.offsetTop;
      if (top < side.scrollTop || top > side.scrollTop + side.clientHeight - 60) {
        side.scrollTo({ top: Math.max(0, top - 120), behavior: "smooth" });
      }
    }
  }

  /* ---------- sidebar ---------- */
  function openSidebar() {
    els.sidebar.classList.add("open");
    els.backdrop.hidden = false;
    requestAnimationFrame(() => els.backdrop.classList.add("show"));
  }

  function closeSidebar() {
    els.sidebar.classList.remove("open");
    els.backdrop.classList.remove("show");
    setTimeout(() => {
      if (!els.sidebar.classList.contains("open")) els.backdrop.hidden = true;
    }, 250);
  }

  els.menuBtn.addEventListener("click", openSidebar);
  els.closeSidebar.addEventListener("click", closeSidebar);
  els.backdrop.addEventListener("click", closeSidebar);
  els.tocJump.addEventListener("click", openSidebar);
  els.openTocFromCover.addEventListener("click", () => {
    enterReader(currentId);
    openSidebar();
  });

  /* ---------- search ---------- */
  els.searchInput.addEventListener("input", () => {
    const q = els.searchInput.value.trim().toLowerCase();
    let hits = 0;
    els.toc.querySelectorAll("a").forEach((a) => {
      const title = (a.dataset.title || "").toLowerCase();
      const pageId = a.dataset.pageId;
      let match = !q || title.includes(q);
      if (q && pageId && pageIndex[pageId] != null) {
        const page = pages[pageIndex[pageId]];
        const body = page.html.replace(/<[^>]+>/g, "").toLowerCase();
        if (body.includes(q)) match = true;
      }
      a.classList.toggle("hidden", !match);
      if (match && q) hits += 1;
    });
    if (q) notify(hits ? `找到 ${hits} 条相关目录` : "没有找到相关内容");
  });

  /* ---------- reading ---------- */
  function enterReader(pageId, restoreScroll = false) {
    coverLocked = true;
    document.body.classList.add("cover-done", "reading");
    els.cover.hidden = true;
    els.reader.hidden = false;
    localStorage.setItem(STORAGE.entered, "1");
    window.scrollTo(0, 0);
    openPage(pageId || pages[0].id, restoreScroll);
  }

  function showCover() {
    coverLocked = false;
    document.body.classList.remove("cover-done", "reading");
    els.reader.hidden = true;
    els.cover.hidden = false;
    closeSidebar();
    window.scrollTo(0, 0);
    els.coverInner.style.transform = "";
    els.coverInner.style.opacity = "1";
    els.quoteStage.classList.remove("visible");
    updateCoverByScroll();
  }

  function openPage(pageId, restoreScroll = false) {
    const idx = pageIndex[pageId];
    if (idx == null) return;
    currentId = pageId;
    const page = pages[idx];

    els.pageContent.innerHTML = page.html;
    els.pageLabel.textContent = page.title;
    els.partLabel.textContent = page.part || "正文";

    // replay enter animation
    els.page.style.animation = "none";
    // force reflow
    void els.page.offsetWidth;
    els.page.style.animation = "";

    const prev = pages[idx - 1];
    const next = pages[idx + 1];
    els.prevBtn.disabled = !prev;
    els.nextBtn.disabled = !next;
    els.prevTitle.textContent = prev ? prev.title : "已是第一篇";
    els.nextTitle.textContent = next ? next.title : "已是最后一篇";

    setActiveToc(pageId);
    localStorage.setItem(STORAGE.page, pageId);
    history.replaceState(null, "", `#${pageId}`);

    if (restoreScroll) {
      const y = Number(localStorage.getItem(STORAGE.scroll) || 0);
      requestAnimationFrame(() => window.scrollTo(0, y));
    } else {
      window.scrollTo(0, 0);
      localStorage.setItem(STORAGE.scroll, "0");
    }

    updateProgress();
  }

  function go(delta) {
    const idx = pageIndex[currentId];
    const target = pages[idx + delta];
    if (target) openPage(target.id);
  }

  els.prevBtn.addEventListener("click", () => go(-1));
  els.nextBtn.addEventListener("click", () => go(1));
  els.startRead.addEventListener("click", () => enterReader(lastPage ? lastPage.id : pages[0].id, !!lastPage));
  els.enterBook.addEventListener("click", () => enterReader(pages[0].id));
  els.backCover.addEventListener("click", showCover);

  /* ---------- progress / resume scroll ---------- */
  function updateProgress() {
    const doc = document.documentElement;
    const max = doc.scrollHeight - doc.clientHeight;
    const ratio = max > 0 ? doc.scrollTop / max : 0;
    els.progress.style.width = `${clamp(ratio, 0, 1) * 100}%`;
    if (document.body.classList.contains("cover-done")) {
      localStorage.setItem(STORAGE.scroll, String(doc.scrollTop));
    }
  }

  window.addEventListener("scroll", updateProgress, { passive: true });

  /* ---------- keyboard ---------- */
  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeSidebar();
    if (!document.body.classList.contains("cover-done")) return;
    if (e.key === "ArrowLeft") go(-1);
    if (e.key === "ArrowRight") go(1);
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "f") {
      e.preventDefault();
      openSidebar();
      els.searchInput.focus();
      els.searchInput.select();
    }
  });

  /* ---------- visit stats (不蒜子) ---------- */
  function syncVisitStats() {
    const pv = document.getElementById("busuanzi_value_site_pv");
    const uv = document.getElementById("busuanzi_value_site_uv");
    const coverStats = document.getElementById("visitStats");
    const sideStats = document.getElementById("sidebarStats");
    const sidePv = document.getElementById("sidebarPv");
    const sideUv = document.getElementById("sidebarUv");
    const pvText = pv?.textContent?.trim();
    const uvText = uv?.textContent?.trim();
    if (!pvText && !uvText) return false;
    if (coverStats) coverStats.hidden = false;
    if (sideStats) sideStats.hidden = false;
    if (sidePv && pvText) sidePv.textContent = pvText;
    if (sideUv && uvText) sideUv.textContent = uvText;
    return true;
  }

  let statsTries = 0;
  const statsTimer = setInterval(() => {
    statsTries += 1;
    if (syncVisitStats() || statsTries > 40) clearInterval(statsTimer);
  }, 400);

  /* ---------- boot ---------- */
  const hash = decodeURIComponent(location.hash.replace(/^#/, ""));
  if (hash && pageIndex[hash] != null) {
    enterReader(hash, true);
  } else if (location.search.includes("read=1") && lastPage) {
    enterReader(lastPage.id, true);
  }
})();
