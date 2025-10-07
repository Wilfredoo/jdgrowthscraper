# JD Growth Scraper Makefile

.PHONY: run install setup clean help

# Default target
help:
	@echo "Available commands:"
	@echo "  make run     - Run the Facebook login script"
	@echo "  make install - Install Python dependencies"
	@echo "  make setup   - Set up the project (install deps + copy env)"
	@echo "  make clean   - Clean up temporary files"
	@echo "  make help    - Show this help message"

# Run the login script
run:
	@echo "🚀 Running Facebook Login Script..."
	python3 simple_login.py

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	pip3 install -r requirements.txt

# Setup project
setup: install
	@echo "⚙️ Setting up project..."
	@if [ ! -f .env ]; then \
		echo "📄 Creating .env file from template..."; \
		cp .env.example .env; \
		echo "✏️ Please edit .env file with your Facebook credentials"; \
	else \
		echo "✅ .env file already exists"; \
	fi

# Clean temporary files
clean:
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf logs/*.log 2>/dev/null || true