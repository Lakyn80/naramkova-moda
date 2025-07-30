// 📁 src/components/ChatWidgetLoader.jsx
import { useEffect } from "react";

export default function ChatWidgetLoader() {
  useEffect(() => {
    const script = document.createElement("script");
    script.src = "https://lakyn80.github.io/ai_chatbot_widget/chat-widget.js";
    script.async = true;

    // ✅ Inicializace po načtení skriptu
    script.onload = () => {
      if (window.ChatbotWidget) {
        window.ChatbotWidget.init({
          welcomeMessage: "Dobrý den! Jak vám mohu pomoci s výběrem náramku 💝",
          accentColor: "#ec4899", // růžová pro Náramkovou Módu
          position: "right",      // nebo "left"
        });
      }
    };

    document.body.appendChild(script);

    // ✅ Čistící funkce při odstranění komponenty
    return () => {
      document.body.removeChild(script);
    };
  }, []);

  return null; // Nevrací žádný HTML obsah
}
