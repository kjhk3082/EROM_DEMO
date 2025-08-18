module.exports = {
  apps: [
    {
      name: 'streamlit-app',
      script: 'streamlit',
      args: 'run streamlit_app.py --server.port 8501 --server.address 0.0.0.0',
      interpreter: 'python3',
      env: {
        PORT: 8501
      }
    },
    {
      name: 'flask-app',
      script: 'enhanced_web_chatbot.py',
      interpreter: 'python3',
      env: {
        PORT: 8080
      }
    }
  ]
};