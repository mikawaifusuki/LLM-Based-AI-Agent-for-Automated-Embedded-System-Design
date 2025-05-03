# LLM-Based AI Agent for Automated Embedded System Design: A Case Study on 8051 Microcontroller Architecture

👉 For implementation details and code usage instructions, please refer to the dedicated code README: [embedded-agent/README.md](https://github.com/mikawaifusuki/LLM-Based-AI-Agent-for-Automated-Embedded-System-Design/blob/main/embedded-agent/README.md)

## Abstract

Traditionally, the design of embedded systems requires the collaborative development and iterative verification of software and hardware, which is very time-consuming and demands domain expertise. Beginners often have a high threshold when building systems like the 8051 single-chip microcomputer, and experienced engineers also find it difficult to avoid repetitive work, which affects the development efficiency.

Against this background, this paper introduces an LLM-based AI agent, which can automate the design of embedded systems based on the 8051 microcontroller, from natural language specifications to simulation verification. This agent uses LangChain for multi-step orchestration and retrieval enhancement generation (RAG) pipelines and can perform the following tasks:

Component selection from a custom knowledge base

Rule-based schematic generation

Embedded C code synthesis and compilation

Co-simulation with Proteus EDA software

Experimental evaluation on benchmark tasks shows a 50–80% reduction in development time compared to human engineers, with high compilation and simulation success rates. This approach demonstrates the viability of AI agents in embedded system co-design, significantly accelerating prototyping.

## Table of Contents

[Introduction](#Introduction) 

[Related Work](#Related-Work)  

[System Architecture & Methodology](#System-Architecture--Methodology)  

[Agent Model Design](#Agent-Model-Design)  

[Experimental Results](#Experimental-Results)  

[Discussion and Future Work](#Discussion-and-Future-Work)  

[References](#References)  

<a id="Introduction"></a>  
## Introduction

Designing embedded systems like the 8051 involves:

Selecting peripherals (sensors, actuators)

Circuit design and verification

Writing and debugging firmware

Problem:

Requires expertise and iterative testing

Time-consuming due to manual EDA and tool integration

Solution:

We propose an AI agent using LLM + LangChain + Proteus to fully automate this workflow:

Input: High-level task description (e.g., "Monitor temperature and turn on a fan")

Output: Verified circuit schematic + compiled firmware + simulation results

<a id="Related-Work"></a>  
## Related Work

LLMs in EDA: LLMs have generated HDL, debugged code, and built testbenches.

LLM agents: ReAct & LangChain enable reasoning-action loops with external tool use.

Design assistants: Tools like STM32CubeMX, Flux Copilot automate part of the design, but lack end-to-end capabilities.

Our contribution:

First to combine hardware schematic, firmware code, and closed-loop simulation into an autonomous agent for 8051-based systems.

<a id="System-Architecture--Methodology"></a>  
## System Architecture & Methodology

**Overview**

 **1.graph**

    A[User Spec (Natural Language)] --> B[LLM Agent via LangChain]
    
    B --> C[Component Knowledge Base (RAG)]
    
    B --> D[Circuit Schematic Generator (Rules)]
    
    B --> E[Firmware Generator (C Code)]
    
    E --> F[SDCC Compiler]
    
    F --> G[Hex Firmware File]
    
    D --> H[Proteus Simulation Setup]
    
    G --> H
    
    H --> I[Simulation Verification]
    
    I -->|Pass| J[Final Design Output]
    
    I -->|Fail| B

**2.Framework**

![image](https://github.com/user-attachments/assets/64df64ee-c99f-4090-a2f9-60e4209e323d)


**3.Steps**

Analyze Requirements

Component Retrieval via RAG

Schematic Construction (Rule-based logic)

C Code Generation for 8051

Compilation via SDCC

Simulation via Proteus VSM

Loop Until Specification Satisfied

<a id="Agent-Model-Design"></a>  
## Agent Model Design

-**LLM Agent via LangChain**

    Uses ReAct-style prompting

    Tools used:

    KnowledgeBaseTool

    CompilerTool

    SimulatorTool

-**Component Knowledge Base (RAG)**

    JSON entries + text from datasheets

    Indexed with FAISS vector database

    Reduces hallucination, ensures factual wiring/code

-**Rule-Based Schematic Generator**

    Inserts resistors, capacitors, pull-ups, etc.

    Ensures electrical correctness

    Converts netlist into Proteus design file

-**Code Generation + Compilation**

    C code for 8051 (reg51.h, loops, ADC logic, etc.)

    Compiled using SDCC

    Error correction loop via LLM: uses compiler error as feedback

-**Simulation in Proteus**

    Scripted update of .pdsprj + .dsn files

    Virtual instruments for output checking (e.g., LED voltage, UART)

    Agent checks logic analyzer / terminal logs to verify behavior

<a id="Experimental-Results"></a>  
## Experimental Results


Tasks

| Task ID | Description          | Complexity |
| ------- | -------------------- | ---------- |
| T1      | LED Blink            | Low        |
| T2      | Temp Monitor + Alarm | Medium     |
| T3      | Keypad + LCD         | Medium     |
| T4      | Motor PWM + Display  | High       |
| T5      | Sensor + RF Comm     | Very High  |

![image](https://github.com/user-attachments/assets/c3b1c9a8-bdf1-4a4c-b464-fcf0ff872a32)


Results Summary

| Metric                | Human Avg | Agent Avg                   |
| --------------------- | --------- | --------------------------- |
| Design Time (mins)    | 60–120    | 20–60                       |
| Compile Attempts      | 1.1       | 1.2                         |
| Simulation Iterations | \~2.0     | 1.5                         |
| Success Rate          | 100%      | 100% (with 1 clarification) |

![image](https://github.com/user-attachments/assets/d4047799-6283-4fc9-9f53-f43a6ef888ab)



# Observations

Agent is faster, especially in complex tasks

Retrieval and rule modules prevent dumb mistakes

Code quality is functional but not always optimal

<a id="Discussion-and-Future-Work"></a>  
## Discussion and Future Work

**Benefits**

Democratizes embedded design

Reduces prototyping time

Enables system-level closed-loop reasoning

**Limitations**

No multi-objective optimization (e.g. power/cost)

Limited by KB coverage

Doesn't handle PCB layout (yet)

**Future Work**

Add power/cost trade-off objectives

Extend to multi-agent setups (hardware/software agents)

Add formal verification tools (static analyzers, model checkers)

Expand to Arduino, ARM, FPGA

Support human-in-the-loop design with constraint injection

<a id="References"></a>  
## References

Xu et al., LLM-Aided Efficient Hardware Design Automation, arXiv:2410.18582, 2024

Yao et al., ReAct: Reasoning and Acting in Language Models, arXiv:2210.03629, 2022

Lewis et al., Retrieval-Augmented Generation for NLP, NeurIPS, 2020

Haug et al., Automated HAL Code for MCUs, arXiv:2502.18905, 2025

Fu et al., GPT4AIGChip: AI Accelerator Design, arXiv:2309.10730, 2023

Labcenter Electronics, Proteus Design Suite, labcenter.com

Pedrido, LLMs Programming Arduino with CrewAI, The Neural Maze, 2023

Instructables, 8051 with SDCC, 2019

📥 For full code, examples, and Proteus files, visit the repository /embedded-agent folder.


