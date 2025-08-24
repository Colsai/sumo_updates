const OpenAI = require('openai');

class AIProcessor {
  constructor(apiKey) {
    this.openai = new OpenAI({
      apiKey: apiKey
    });
  }

  async createTweetLikeSummary(newsItem) {
    try {
      const prompt = `Convert this sumo wrestling news into a concise, engaging tweet-like summary (max 280 characters). Make it informative but casual and exciting:

Title: ${newsItem.title}
URL: ${newsItem.url}
Additional context: ${newsItem.content || ''}

Format the response as a single tweet that captures the essence of the news. Include relevant sumo terminology and emojis if appropriate. Make it exciting for sumo fans!`;

      const response = await this.openai.chat.completions.create({
        model: 'gpt-3.5-turbo',
        messages: [{ role: 'user', content: prompt }],
        max_tokens: 100,
        temperature: 0.7
      });

      const summary = response.choices[0].message.content.trim();
      
      // Ensure it's under 280 characters
      return summary.length > 280 ? summary.substring(0, 277) + '...' : summary;
      
    } catch (error) {
      console.error('Error creating AI summary:', error.message);
      // Fallback to a simple summary
      return this.createFallbackSummary(newsItem);
    }
  }

  createFallbackSummary(newsItem) {
    const title = newsItem.title;
    if (title.length <= 280) {
      return `🥋 ${title}`;
    }
    return `🥋 ${title.substring(0, 275)}...`;
  }

  async processBatch(newsItems) {
    const summaries = [];
    
    for (const item of newsItems) {
      console.log(`Processing: ${item.title}`);
      const summary = await this.createTweetLikeSummary(item);
      
      summaries.push({
        ...item,
        summary: summary,
        processedAt: new Date().toISOString()
      });
      
      // Rate limiting - wait 1 second between API calls
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    return summaries;
  }

  async createEmailDigest(summaries) {
    try {
      const newsContent = summaries.map((item, index) => 
        `${index + 1}. ${item.summary}\n   📰 Read more: ${item.url}`
      ).join('\n\n');

      const prompt = `Create an engaging email subject line and introduction for a sumo wrestling news digest. The email contains ${summaries.length} news items. Make it enthusiastic and appealing to sumo fans.

News items:
${newsContent}

Provide:
1. SUBJECT: [compelling subject line under 50 characters]
2. INTRO: [2-3 sentence introduction paragraph]`;

      const response = await this.openai.chat.completions.create({
        model: 'gpt-3.5-turbo',
        messages: [{ role: 'user', content: prompt }],
        max_tokens: 150,
        temperature: 0.7
      });

      const result = response.choices[0].message.content.trim();
      const lines = result.split('\n');
      
      let subject = 'Sumo Wrestling News Update';
      let intro = 'Here are the latest updates from the world of sumo wrestling!';
      
      lines.forEach(line => {
        if (line.startsWith('SUBJECT:')) {
          subject = line.replace('SUBJECT:', '').trim();
        } else if (line.startsWith('INTRO:')) {
          intro = line.replace('INTRO:', '').trim();
        }
      });

      return { subject, intro };
      
    } catch (error) {
      console.error('Error creating email digest:', error.message);
      return {
        subject: 'Sumo Wrestling News Update',
        intro: 'Here are the latest updates from the world of sumo wrestling!'
      };
    }
  }
}

module.exports = AIProcessor;