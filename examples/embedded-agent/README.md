# 8051 Embedded System Design Agent

An intelligent agent system that automates the design of 8051 embedded systems. This project enables users to describe an embedded system in natural language and automatically generates the component selection, circuit design, C code, compilation, and simulation.

## Features

- **Natural Language Interface**: Describe your desired embedded system in plain English
- **Knowledge Base**: Intelligent component selection based on a comprehensive database
- **Automated Circuit Design**: Generate circuit diagrams and netlists
- **8051 C Code Generation**: Automatically create 8051 C code based on requirements
- **Compilation**: Automatically compile code using SDCC
- **Simulation**: Run simulations in Proteus and analyze results
- **Feedback Loop**: Automatically fix errors and refine designs

## Architecture

The system is built on:
- LangChain Agent Framework
- OpenAI GPT-4o for reasoning
- FAISS for vector search knowledge base
- SDCC compiler for 8051 code
- Proteus for circuit simulation

## Project Structure

```
embedded-agent/
├── backend/
│   ├── agent/
│   │   ├── main_agent.py         # LangChain agent main logic
│   │   ├── tools/
│   │   │   ├── knowledge_base.py # FAISS + component DB search
│   │   │   ├── compiler.py       # SDCC compiler integration
│   │   │   └── simulator.py      # Proteus simulation interface
│   ├── kb/
│   │   ├── components.jsonl      # Component database
│   │   └── datasheets/           # Additional component docs
│   ├── scripts/
│   │   ├── update_proteus.py     # Proteus file updater
│   │   └── run_simulation.bat    # Simulation batch script
│   ├── outputs/                  # Generated artifacts
│   └── server.py                 # FastAPI server
├── frontend/
│   └── web-ui/                   # React web interface
├── docker-compose.yml            # Docker Compose configuration
└── README.md
```

## Installation

### Prerequisites

- Python 3.9+
- Node.js 16+
- SDCC (Small Device C Compiler)
- Proteus 8 Professional (for simulation)
- Docker and Docker Compose (optional for containerized setup)

### Method 1: Docker Compose (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/embedded-agent.git
   cd embedded-agent
   ```

2. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```

3. Edit the `.env` file and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. Start the services using Docker Compose:
   ```bash
   docker-compose up -d
   ```

5. Access the web interface at `http://localhost:3000`

### Method 2: Manual Setup

#### Backend Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Set environment variables:
   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```

4. Start the backend server:
   ```bash
   uvicorn server:app --host 0.0.0.0 --port 8000 --reload
   ```

#### Frontend Setup

1. Install dependencies:
   ```bash
   cd frontend/web-ui
   npm install
   ```

2. Start the development server:
   ```bash
   npm start
   ```

3. Access the web interface at `http://localhost:3000`

## Usage

1. Enter a natural language description of your desired 8051 embedded system
2. The agent will analyze the requirements and determine needed components
3. It will design a circuit and generate 8051 C code
4. The code will be compiled and simulated
5. Results and generated artifacts will be displayed

### Example Request

```
Design a system that uses an 8051 microcontroller and an LM35 temperature sensor.
The system should read the temperature once per second.
If the temperature exceeds 30°C, turn on an LED and activate a cooling fan.
Otherwise, keep the LED off and the fan off.
Display the current temperature on the UART.
```

## Simulation Requirements

For full simulation capabilities, you need:

1. SDCC (Small Device C Compiler):
   - Install from [SDCC Website](http://sdcc.sourceforge.net/)
   - Make sure it's in your system PATH

2. Proteus 8 Professional:
   - Commercial software from Labcenter Electronics
   - Update the Proteus path in the `.env` file if installed in a non-default location

## API Endpoints

The backend server exposes the following endpoints:

- `GET /`: Root endpoint, returns a welcome message
- `POST /design`: Create a new design task
- `GET /design/{task_id}`: Get the status of a design task
- `GET /artifacts/{task_id}/{artifact_type}`: Download a specific artifact

## Troubleshooting

### Common Issues

1. **OpenAI API Key Issues**:
   - Make sure your API key is correctly set in the `.env` file or as an environment variable
   - Check that the key has sufficient quota and permissions

2. **SDCC Compiler Issues**:
   - Verify SDCC is properly installed and in your PATH
   - Check compile errors in the agent's response

3. **Proteus Simulation Issues**:
   - Verify the correct Proteus path in your environment configuration
   - Ensure you have a valid Proteus license

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- LangChain for the agent framework
- OpenAI for the GPT-4o model
- SDCC team for the 8051 compiler
- Labcenter Electronics for Proteus 