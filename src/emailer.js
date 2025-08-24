const nodemailer = require('nodemailer');

class EmailSender {
  constructor(config) {
    this.config = config;
    this.transporter = nodemailer.createTransporter({
      host: config.host,
      port: config.port,
      secure: false, // true for 465, false for other ports
      auth: {
        user: config.user,
        pass: config.pass
      }
    });
  }

  async sendNewsDigest(summaries, emailMeta) {
    try {
      if (summaries.length === 0) {
        console.log('No news to send');
        return;
      }

      const htmlContent = this.generateHTMLEmail(summaries, emailMeta);
      const textContent = this.generateTextEmail(summaries, emailMeta);

      const mailOptions = {
        from: `"Sumo News Bot" <${this.config.user}>`,
        to: this.config.to,
        subject: emailMeta.subject,
        text: textContent,
        html: htmlContent
      };

      console.log('Sending email...');
      const info = await this.transporter.sendMail(mailOptions);
      console.log('Email sent successfully:', info.messageId);
      
      return { success: true, messageId: info.messageId };
      
    } catch (error) {
      console.error('Error sending email:', error.message);
      return { success: false, error: error.message };
    }
  }

  generateHTMLEmail(summaries, emailMeta) {
    const newsItems = summaries.map((item, index) => `
      <div style="margin-bottom: 20px; padding: 15px; border-left: 4px solid #d2691e; background-color: #fafafa;">
        <div style="font-size: 16px; margin-bottom: 8px; color: #333;">
          <strong>${index + 1}.</strong> ${item.summary}
        </div>
        <div style="font-size: 12px; color: #666; margin-bottom: 5px;">
          📅 ${new Date(item.date).toLocaleDateString()}
        </div>
        <div>
          <a href="${item.url}" style="color: #d2691e; text-decoration: none; font-weight: bold;">
            📰 Read full article →
          </a>
        </div>
      </div>
    `).join('');

    return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>${emailMeta.subject}</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
      <div style="background-color: #d2691e; color: white; padding: 20px; text-align: center; margin-bottom: 30px;">
        <h1 style="margin: 0; font-size: 24px;">🥋 Sumo Wrestling News</h1>
        <p style="margin: 10px 0 0 0; font-size: 14px;">Your daily digest of sumo updates</p>
      </div>
      
      <div style="margin-bottom: 20px;">
        <p style="font-size: 16px; margin-bottom: 20px;">${emailMeta.intro}</p>
      </div>
      
      ${newsItems}
      
      <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #666; font-size: 12px;">
        <p>This digest was automatically generated from <a href="https://www.sumo.or.jp/En/" style="color: #d2691e;">sumo.or.jp</a></p>
        <p>Generated on ${new Date().toLocaleDateString()} at ${new Date().toLocaleTimeString()}</p>
      </div>
    </body>
    </html>
    `;
  }

  generateTextEmail(summaries, emailMeta) {
    const newsItems = summaries.map((item, index) => 
      `${index + 1}. ${item.summary}\n   📅 ${new Date(item.date).toLocaleDateString()}\n   📰 ${item.url}\n`
    ).join('\n');

    return `🥋 SUMO WRESTLING NEWS DIGEST

${emailMeta.intro}

${newsItems}

---
This digest was automatically generated from sumo.or.jp
Generated on ${new Date().toLocaleDateString()} at ${new Date().toLocaleTimeString()}`;
  }

  async testConnection() {
    try {
      await this.transporter.verify();
      console.log('Email connection verified successfully');
      return true;
    } catch (error) {
      console.error('Email connection failed:', error.message);
      return false;
    }
  }
}

module.exports = EmailSender;