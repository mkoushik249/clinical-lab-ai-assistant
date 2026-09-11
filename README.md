🧪 Clinical Laboratory AI AssistantSecure, grounded AI access to laboratory tests, specimen guidance, turnaround times, and approved laboratory policies.





Production-oriented internal AI assistant built with RAG, controlled SQL retrieval, native LLM tool calling, and AWS serverless infrastructure.

Overview
The Clinical Laboratory AI Assistant is designed as an internal tool for quickly retrieving approved laboratory information through natural-language questions.
Instead of searching separate databases and policy documents, users can ask questions such as:

What is the turnaround time for CBC?
What specimen is required for a blood culture?
What is the specimen collection guidance?
The system combines structured PostgreSQL data with RAG-based policy retrieval while restricting the LLM to approved tools and grounded sources.

Data & Safety: This repository uses synthetic/public laboratory information only. No PHI or real patient records are included.

System Architecture

<p align="center"><img src="docs/clinical-lab-ai-architecture.png" alt="clinical Laboratory Ai Assistant Architecture" width ="100%"></p>

Request Flow
Frontend:
User → CloudFront → Private S3 → Next.js
Authentication:
Next.js → Amazon Cognito → JWT → API Gateway
Backend:
API Gateway → AWS Lambda → FastAPI → AI Orchestrator
Structured Data:
AI Orchestrator → Controlled SQL Tool → PostgreSQL
RAG:
AI Orchestrator → Embedding → pgvector → Approved Laboratory Documents
Response:
Retrieved Evidence → OpenAI → Grounded Answer + Sources
How Questions Are Processed
Question Type
Processing Path
Lab test / turnaround time
Agent → SQL Tool → PostgreSQL → Response
Policy / procedure question
Agent → RAG → pgvector → Documents → Response
List available tests
Agent → List Tool → PostgreSQL → Response
Unsupported question
Agent → Safety Check → Controlled No-Data ResponseDeployment Flow
Backend Deployment
Source Code → Docker → Amazon ECR → AWS Lambda → API Gateway
Frontend Deployment
Next.js Build → Private S3 → CloudFront → HTTPS
Database
RDS PostgreSQL → Structured Lab Data + pgvector Embeddings

Docker image → AMD64
Lambda       → ARM64


The deployment image was rebuilt for linux/amd64 and Lambda was aligned to x86_64.
Private VPC Connectivity
Lambda initially lacked permission to create the network interfaces required for VPC connectivity.
The execution role was updated with the appropriate Lambda VPC permissions.
pgvector Initialization
RDS initially rejected the vector schema because the extension had not yet been enabled.
CREATE EXTENSION IF NOT EXISTS vector;
was executed before creating the vector-backed tables.
CloudFront Origin Configuration
CloudFront initially returned AccessDenied because an incorrect /project origin path was configured while the exported frontend files were stored at the S3 bucket root.
The origin path was corrected and the CloudFront cache was invalidated.


Scope
This project demonstrates a production-oriented architecture for an internal clinical laboratory knowledge assistant.
It focuses on:
secure retrieval · grounded AI · controlled data access · production deployment · healthcare AI safety
It does not contain real patient information and is not intended to replace clinical judgment.
Clinical Laboratory AI Assistant
Python · FastAPI · PostgreSQL · pgvector · OpenAI · Docker · AWS · Next.js
