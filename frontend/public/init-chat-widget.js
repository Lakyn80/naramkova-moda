// 📁 public/init-chat-widget.js

window.ChatbotWidget = {
  init: function () {
    new window.ChatWidget({
      apiBaseUrl: "https://aichatbotwidget-production.up.railway.app",
      title: "AI Chatbot",
      introMessage: "Dobrý den! Rádi vám pomůžeme s výběrem náramku 💝",
      placeholder: "Zeptejte se na cokoliv...",
      position: "bottom-right",
      themeColor: "#ec4899"
    });
  }
};
