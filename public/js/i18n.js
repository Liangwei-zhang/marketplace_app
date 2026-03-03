// i18n - Language Toggle
const translations = {
    en: {
        searchPlaceholder: "Search items...",
        sell: "+ Sell",
        chat: "Chat",
        profile: "Profile",
        all: "All",
        electronics: "Electronics",
        clothing: "Clothing",
        furniture: "Furniture",
        books: "Books",
        sports: "Sports",
        games: "Games",
        other: "Other",
        loadMore: "Load More",
        noItems: "No items found",
        home: "Home",
        favorites: "Favorites",
        history: "History",
        publish: "Publish Item",
        title: "Title",
        description: "Description",
        price: "Price",
        category: "Category",
        submit: "Submit",
        cancel: "Cancel"
    },
    zh: {
        searchPlaceholder: "搜索商品...",
        sell: "+ 发布",
        chat: "消息",
        profile: "我的",
        all: "全部",
        electronics: "电子产品",
        clothing: "服装",
        furniture: "家具",
        books: "图书",
        sports: "运动",
        games: "游戏",
        other: "其他",
        loadMore: "加载更多",
        noItems: "暂无商品",
        home: "首页",
        favorites: "收藏",
        history: "浏览",
        publish: "发布商品",
        title: "标题",
        description: "描述",
        price: "价格",
        category: "分类",
        submit: "发布",
        cancel: "取消"
    }
};

let currentLang = localStorage.getItem('lang') || 'en';

function setLang(lang) {
    currentLang = lang;
    localStorage.setItem('lang', lang);
    const btn = document.getElementById('langToggle');
    if(btn) btn.textContent = lang === 'en' ? '中文' : 'EN';
    applyTranslations();
}

function applyTranslations() {
    const t = translations[currentLang];
    // Search
    const searchInput = document.getElementById('searchInput');
    if(searchInput) searchInput.placeholder = t.searchPlaceholder;
    // Header buttons
    const headerActions = document.querySelector('.header-actions');
    if(headerActions) {
        const links = headerActions.querySelectorAll('a');
        if(links[0]) links[0].textContent = t.sell;
        if(links[1]) links[1].textContent = t.chat;
        if(links[2]) links[2].textContent = t.profile;
    }
    // Categories
    const cats = document.querySelectorAll('.category-tag');
    if(cats[0]) cats[0].textContent = t.all;
    if(cats[1]) cats[1].textContent = t.electronics;
    if(cats[2]) cats[2].textContent = t.clothing;
    if(cats[3]) cats[3].textContent = t.furniture;
    if(cats[4]) cats[4].textContent = t.books;
    if(cats[5]) cats[5].textContent = t.sports;
    if(cats[6]) cats[6].textContent = t.games;
    if(cats[7]) cats[7].textContent = t.other;
    // Nav
    const navItems = document.querySelectorAll('.nav-bar .nav-item');
    if(navItems[0]) navItems[0].querySelector('span:last-child').textContent = t.home;
    if(navItems[1]) navItems[1].querySelector('span:last-child').textContent = t.favorites;
    if(navItems[2]) navItems[2].querySelector('span:last-child').textContent = t.history;
    if(navItems[3]) navItems[3].querySelector('span:last-child').textContent = t.chat;
    if(navItems[4]) navItems[4].querySelector('span:last-child').textContent = t.profile;
    // Load more button
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    if(loadMoreBtn) loadMoreBtn.textContent = t.loadMore;
    // Publish page
    const pageTitle = document.querySelector('.page-title');
    if(pageTitle) {
        if(pageTitle.textContent.includes('Publish')) pageTitle.textContent = t.publish;
    }
    // Form labels
    const labels = document.querySelectorAll('label');
    labels.forEach(l => {
        if(l.textContent.includes('Title')) l.textContent = t.title;
        if(l.textContent.includes('Description')) l.textContent = t.description;
        if(l.textContent.includes('Price')) l.textContent = t.price;
        if(l.textContent.includes('Category')) l.textContent = t.category;
    });
    // Buttons
    const submitBtn = document.querySelector('button[type="submit"]');
    if(submitBtn && submitBtn.textContent.includes('Submit')) submitBtn.textContent = t.submit;
    // Set lang attribute
    document.documentElement.lang = currentLang;
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    const btn = document.getElementById('langToggle');
    if(btn) {
        btn.addEventListener('click', function() {
            setLang(currentLang === 'en' ? 'zh' : 'en');
        });
        setLang(currentLang);
    }
});
