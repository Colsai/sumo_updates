const axios = require('axios');
const cheerio = require('cheerio');

class SumoNewsScraper {
  constructor() {
    this.baseUrl = 'https://www.sumo.or.jp/En/';
  }

  async scrapeNews() {
    try {
      console.log('Fetching news from', this.baseUrl);
      const response = await axios.get(this.baseUrl, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
      });

      const $ = cheerio.load(response.data);
      const newsItems = [];

      // Look for news items in various sections
      $('a').each((index, element) => {
        const $link = $(element);
        const href = $link.attr('href');
        const text = $link.text().trim();
        
        // Filter for news-like content
        if (text && href && this.isNewsContent(text, href)) {
          newsItems.push({
            title: text,
            url: this.resolveUrl(href),
            date: this.extractDate(text) || new Date().toISOString().split('T')[0],
            rawText: text
          });
        }
      });

      // Also look for specific news sections or divs
      $('.news-item, .what-new, [class*="news"]').each((index, element) => {
        const $item = $(element);
        const title = $item.find('a').text().trim() || $item.text().trim();
        const href = $item.find('a').attr('href');
        
        if (title && href) {
          newsItems.push({
            title: title,
            url: this.resolveUrl(href),
            date: this.extractDate(title) || new Date().toISOString().split('T')[0],
            rawText: title
          });
        }
      });

      // Remove duplicates and sort by relevance
      const uniqueNews = this.removeDuplicates(newsItems);
      const relevantNews = this.filterRelevantNews(uniqueNews);
      
      console.log(`Found ${relevantNews.length} news items`);
      return relevantNews.slice(0, 5); // Return top 5 items

    } catch (error) {
      console.error('Error scraping news:', error.message);
      return [];
    }
  }

  isNewsContent(text, href) {
    const newsKeywords = [
      'tournament', 'champion', 'promotion', 'sumo', 'wrestler',
      'bout', 'winner', 'result', 'ranking', 'ceremony', 'yokozuna',
      'ozeki', 'sekiwake', 'komusubi', 'maegashira', 'juryo'
    ];
    
    const lowercaseText = text.toLowerCase();
    const lowercaseHref = href.toLowerCase();
    
    return newsKeywords.some(keyword => 
      lowercaseText.includes(keyword) || lowercaseHref.includes(keyword)
    ) && text.length > 10 && text.length < 200;
  }

  extractDate(text) {
    // Look for date patterns in the text
    const dateRegex = /(\d{4}[-\/]\d{1,2}[-\/]\d{1,2})|(\d{1,2}[-\/]\d{1,2}[-\/]\d{4})/;
    const match = text.match(dateRegex);
    if (match) {
      return new Date(match[0]).toISOString().split('T')[0];
    }
    return null;
  }

  resolveUrl(href) {
    if (href.startsWith('http')) {
      return href;
    }
    if (href.startsWith('/')) {
      return 'https://www.sumo.or.jp' + href;
    }
    return 'https://www.sumo.or.jp/En/' + href;
  }

  removeDuplicates(newsItems) {
    const seen = new Set();
    return newsItems.filter(item => {
      const key = item.title.toLowerCase().trim();
      if (seen.has(key)) {
        return false;
      }
      seen.add(key);
      return true;
    });
  }

  filterRelevantNews(newsItems) {
    // Filter out navigation items, generic links, etc.
    return newsItems.filter(item => {
      const title = item.title.toLowerCase();
      const excludePatterns = [
        'home', 'contact', 'about', 'privacy', 'terms',
        'site map', 'english', 'japanese', 'menu'
      ];
      
      return !excludePatterns.some(pattern => title.includes(pattern)) &&
             item.title.length > 15 &&
             item.title.length < 150;
    });
  }

  async scrapeArticleContent(url) {
    try {
      const response = await axios.get(url, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
      });

      const $ = cheerio.load(response.data);
      
      // Extract main content
      const content = $('article, .content, .main, p').map((i, el) => $(el).text()).get().join(' ');
      
      return content.trim().slice(0, 1000); // Limit content length
    } catch (error) {
      console.error('Error scraping article:', error.message);
      return '';
    }
  }
}

module.exports = SumoNewsScraper;