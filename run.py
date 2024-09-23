from app import app

if __name__ == "__main__":
    try:
        app.run(debug=True)
    except Exception as e:
        print(f"Erro ao iniciar o servidor: {e}")
