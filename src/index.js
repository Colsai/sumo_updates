require('dotenv').config();
const SumoNewsScraper = require('./scraper');
const AIProcessor = require('./ai-processor');
const EmailSender = require('./emailer');

class SumoNewsApp {
  constructor() {
    this.scraper = new SumoNewsScraper();
    this.aiProcessor = new AIProcessor(process.env.OPENAI_API_KEY);
    this.emailSender = new EmailSender({
      host: process.env.EMAIL_HOST,
      port: parseInt(process.env.EMAIL_PORT),
      user: process.env.EMAIL_USER,
      pass: process.env.EMAIL_PASS,
      to: process.env.EMAIL_TO
    });
  }

  async run() {
    try {
      console.log('🥋 Starting Sumo News Digest Generation...');
      console.log('='.repeat(50));

      // Step 1: Scrape news
      console.log('📰 Scraping news from sumo.or.jp...');
      const newsItems = await this.scraper.scrapeNews();
      
      if (newsItems.length === 0) {
        console.log('No news items found. Exiting.');
        return;
      }

      console.log(`Found ${newsItems.length} news items:`);
      newsItems.forEach((item, index) => {
        console.log(`  ${index + 1}. ${item.title.substring(0, 60)}...`);
      });

      // Step 2: Enhance with article content (optional)
      console.log('\n📖 Fetching article content...');
      for (let item of newsItems) {
        item.content = await this.scraper.scrapeArticleContent(item.url);
        await new Promise(resolve => setTimeout(resolve, 1000)); // Rate limiting
      }

      // Step 3: Process with AI
      console.log('\n🤖 Processing with AI...');
      const processedItems = await this.aiProcessor.processBatch(newsItems);
      
      console.log('AI summaries generated:');
      processedItems.forEach((item, index) => {
        console.log(`  ${index + 1}. ${item.summary}`);
      });

      // Step 4: Create email digest
      console.log('\n✉️ Creating email digest...');
      const emailMeta = await this.aiProcessor.createEmailDigest(processedItems);
      console.log(`Email subject: ${emailMeta.subject}`);
      console.log(`Email intro: ${emailMeta.intro}`);

      // Step 5: Send email
      console.log('\n📧 Sending email...');
      const result = await this.emailSender.sendNewsDigest(processedItems, emailMeta);
      
      if (result.success) {
        console.log('✅ Email sent successfully!');
        console.log(`Message ID: ${result.messageId}`);
      } else {
        console.error('❌ Failed to send email:', result.error);
      }

      console.log('\n🎉 Sumo News Digest completed!');
      
    } catch (error) {
      console.error('❌ Application error:', error.message);
      console.error(error.stack);
    }
  }

  async testComponents() {
    console.log('🧪 Testing application components...\n');

    // Test email connection
    console.log('Testing email connection...');
    const emailOk = await this.emailSender.testConnection();
    console.log(`Email: ${emailOk ? '✅ OK' : '❌ Failed'}\n`);

    // Test scraper
    console.log('Testing news scraper...');
    try {
      const news = await this.scraper.scrapeNews();
      console.log(`Scraper: ✅ OK (found ${news.length} items)\n`);
    } catch (error) {
      console.log(`Scraper: ❌ Failed (${error.message})\n`);
    }

    // Test AI (if API key provided)
    if (process.env.OPENAI_API_KEY) {
      console.log('Testing AI processor...');
      try {
        const testSummary = await this.aiProcessor.createTweetLikeSummary({
          title: 'Test Sumo Tournament Results',
          url: 'https://example.com',
          content: 'Test content'
        });
        console.log(`AI: ✅ OK (${testSummary.substring(0, 50)}...)\n`);
      } catch (error) {
        console.log(`AI: ❌ Failed (${error.message})\n`);
      }
    } else {
      console.log('AI: ⚠️ Skipped (no API key)\n');
    }
  }
}

// Command line interface
const args = process.argv.slice(2);
const app = new SumoNewsApp();

if (args.includes('--test')) {
  app.testComponents();
} else if (args.includes('--help')) {
  console.log(`
🥋 Sumo News Emailer

Usage:
  node src/index.js           - Run the main application
  node src/index.js --test    - Test all components
  node src/index.js --help    - Show this help

Environment variables required:
  OPENAI_API_KEY    - Your OpenAI API key
  EMAIL_HOST        - SMTP server (e.g., smtp.gmail.com)
  EMAIL_PORT        - SMTP port (e.g., 587)
  EMAIL_USER        - Your email address
  EMAIL_PASS        - Your email password/app password
  EMAIL_TO          - Recipient email address

Copy .env.example to .env and fill in your values.
  `);
} else {
  app.run();
}

module.exports = SumoNewsApp;