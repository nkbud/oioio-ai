# OIOIO AI - Intelligent Assistant

A modern, responsive AI chat application built with vanilla JavaScript, featuring a clean interface and intelligent conversation capabilities.

## 🚀 Features

- **Modern Chat Interface**: Clean, responsive design with real-time messaging
- **Intelligent AI Responses**: Contextual AI assistant with natural conversation flow
- **Persistent Conversations**: Automatic saving and loading of chat history
- **Mobile Responsive**: Optimized for desktop, tablet, and mobile devices
- **Accessibility Ready**: ARIA labels and keyboard navigation support
- **GitHub Pages Compatible**: Pure client-side application, no server required

## 🌟 Live Demo

Visit the live application at [https://nkbud.github.io/oioio-ai](https://nkbud.github.io/oioio-ai)

## 🛠️ Technology Stack

- **Frontend**: HTML5, CSS3, Vanilla JavaScript (ES6+)
- **Styling**: CSS Custom Properties, Flexbox, CSS Grid
- **Architecture**: Modular class-based JavaScript
- **Storage**: LocalStorage for conversation persistence
- **Deployment**: GitHub Pages static hosting

## 📁 Project Structure

```
oioio-ai/
├── index.html          # Main application entry point
├── css/
│   └── styles.css      # Application styles with CSS variables
├── js/
│   └── app.js          # Main application logic and AI engine
└── README.md           # Project documentation
```

## 🚀 Getting Started

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/nkbud/oioio-ai.git
   cd oioio-ai
   ```

2. Open `index.html` in your browser or serve it using a local server:
   ```bash
   # Using Python
   python -m http.server 8000
   
   # Using Node.js
   npx serve .
   
   # Using PHP
   php -S localhost:8000
   ```

3. Navigate to `http://localhost:8000` to view the application

### Deployment

The application is automatically deployed to GitHub Pages. Any changes pushed to the main branch will be reflected on the live site.

## 💡 Usage

1. **Start Chatting**: Type a message in the input field and press Enter
2. **Quick Actions**: Use the suggested prompts on the welcome screen
3. **Keyboard Shortcuts**: 
   - Enter: Send message
   - Shift+Enter: New line in message
4. **Clear History**: Click the trash icon to start fresh

## 🔧 Customization

### Theming
Modify CSS custom properties in `css/styles.css`:

```css
:root {
    --primary-color: #2563eb;        /* Main brand color */
    --background-color: #ffffff;     /* Background */
    --text-primary: #1e293b;         /* Primary text */
    /* ... other variables */
}
```

### AI Responses
Customize AI behavior in `js/app.js` by modifying the `generateAIResponse()` method.

### Adding Features
The modular architecture makes it easy to extend functionality:
- Add new UI components
- Integrate external APIs
- Implement additional AI capabilities

## 🔒 Privacy & Security

- **No Data Transmission**: All conversations are stored locally in your browser
- **No External APIs**: Currently uses simulated AI responses (can be extended)
- **Privacy First**: No tracking or analytics by default

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature/new-feature`
5. Submit a pull request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🔮 Future Enhancements

- [ ] Integration with real AI APIs (OpenAI, Anthropic, etc.)
- [ ] File upload and processing capabilities
- [ ] Multiple conversation threads
- [ ] Export/import conversations
- [ ] Custom AI model selection
- [ ] Voice input/output
- [ ] Advanced markdown rendering
- [ ] Plugin system for extensions

## 📞 Support

For issues, questions, or contributions, please visit our [GitHub Issues](https://github.com/nkbud/oioio-ai/issues) page.

---

Built with ❤️ by the OIOIO AI Team