import Repository from "./Repository";
import { Mail, Globe, User, Code, GraduationCap, Briefcase, Github, Linkedin, Database, Cloud, Monitor, Cpu } from 'lucide-react';

const Portfolio = () => {
    const header = {
        name: "Junsheng (YJ) Ye",
        title: "Software Engineer",
        contact: [
            { icon: <Mail className="w-4 h-4" />, text: "overdosedizzy@gmail.com" },
            { icon: <Linkedin className="w-4 h-4" />, text: "linkedin.com/in/yj-pro", link: "https://linkedin.com/in/yj-pro" },
            { icon: <Github className="w-4 h-4" />, text: "github.com/DizzyDoze", link: "https://github.com/DizzyDoze" },
            { icon: <Globe className="w-4 h-4" />, text: "neuralripper.com", link: "https://neuralripper.com" },
        ]
    };

    const summary = {
        text: "Software Engineer with 3+ years of experience building production AI systems and full-stack applications. Specialized in multi-agent orchestration (LangChain/LangGraph), RAG pipelines with vector databases, and scalable LLM inference. Hands-on fine-tuning experience with transformer models (BERT, GPT-2) and CNNs (ResNet, EfficientNet) using PyTorch. Full-stack across Python, FastAPI, React, and TypeScript."
    };

    const techSkills = {
        languages: ['Python', 'TypeScript', 'JavaScript', 'Java', 'Golang', 'SQL', 'Shell', 'Rust'],
        aiml: ['LangChain', 'LangGraph', 'RAG', 'pgvector', 'Agentic AI', 'MCP', 'LLM Fine-tuning', 'Prompt Engineering', 'PyTorch', 'TensorFlow', 'MLflow', 'LangSmith'],
        backend: ['FastAPI', 'Flask', 'Django', 'Node.js', 'REST APIs', 'WebSocket', 'Microservices'],
        frontend: ['React', 'Next.js', 'TypeScript', 'Vite', 'TailwindCSS', 'Material UI', 'Redux'],
        databases: ['PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch', 'pgvector'],
        cloud: ['AWS (ECS, ECR, S3, RDS, Lambda, VPC, Cognito)', 'Docker', 'Kubernetes', 'Nginx', 'CI/CD', 'Git'],
    };

    const skillIcons: Record<string, React.ReactNode> = {
        languages: <Code className="w-4 h-4 text-cyan-400" />,
        aiml: <Cpu className="w-4 h-4 text-cyan-400" />,
        backend: <Monitor className="w-4 h-4 text-cyan-400" />,
        frontend: <Monitor className="w-4 h-4 text-cyan-400" />,
        databases: <Database className="w-4 h-4 text-cyan-400" />,
        cloud: <Cloud className="w-4 h-4 text-cyan-400" />,
    };

    const skillLabels: Record<string, string> = {
        languages: 'Languages',
        aiml: 'AI/ML',
        backend: 'Backend',
        frontend: 'Frontend',
        databases: 'Databases',
        cloud: 'Cloud/DevOps',
    };

    const education = [
        {
            degree: "M.S. Computer Science",
            school: "University of San Francisco",
            period: "Aug 2023 – May 2026",
            current: false
        },
    ];

    const experience = [
        {
            title: "Machine Learning Engineer Intern",
            company: "LenderToolkit",
            period: "May 2025 – Present",
            current: true,
            achievements: [
                "Architected multi-agent mortgage guidelines platform with FastAPI serving Fannie Mae, Freddie Mac, FHA, VA, USDA guidelines. Implemented LangGraph ReAct agents with AgentFactory pattern for dynamic orchestration",
                "Built production RAG system with pgvector semantic search, Cohere reranking, and AWS Textract for PDF/document extraction, achieving 35% improvement in retrieval precision across 100K+ guideline documents",
                "Designed MCP tool framework with 10+ agentic tools including RAG retrieval, section lookup, web search, OCR. Enabled non-technical users to compose custom mortgage assistants",
                "Implemented end-to-end AWS infrastructure: ECS/Fargate, ECR, S3, RDS PostgreSQL, VPC networking, Cognito JWT auth",
                "Developed async SSE streaming with conversation persistence, achieving sub-100ms first-token latency. Integrated LangSmith for real-time cost analytics and observability across 10K+ daily sessions"
            ]
        },
        {
            title: "Full Stack Software Engineer Intern",
            company: "ValueGlance",
            period: "Feb 2025 – May 2025",
            current: false,
            achievements: [
                "Built core features for financial analytics platform using React, TypeScript, and Vite. Integrated Elasticsearch improving search relevance scores by 40%",
                "Designed RESTful APIs with FastAPI for real-time market data processing. Containerized services with Docker achieving consistent deployments across dev/staging/prod",
                "Automated CI/CD pipelines with GitHub Actions. Managed AWS infrastructure (EC2, S3, Lambda, API Gateway) reducing deployment time from 2 hours to 15 minutes"
            ]
        },
        {
            title: "Teaching Assistant, AI Foundations",
            company: "University of San Francisco",
            period: "Aug 2024 – May 2025",
            current: false,
            achievements: [
                "Supported instruction for 120+ students in search algorithms, decision trees, probabilistic inference, MDPs, reinforcement learning, and neural networks",
                "Guided coding assignments in Python. Led weekly problem-solving sessions. Contributed to course materials and grading"
            ]
        },
        {
            title: "Software Engineer",
            company: "OPPO",
            period: "Mar 2019 – Oct 2020",
            current: false,
            achievements: [
                "Developed backend services with Flask and Django, designing RESTful APIs for the big data platform serving 5 teams, reducing platform usage complaints by 25%",
                "Built data migration platform orchestrating 100 PB of HDFS data and Hive tables across 20+ clusters, reducing data transfer time by 20%",
                "Automated migration tasks with Python and Redis for real-time task tracking, leveraging multiprocessing for concurrent execution",
                "Automated cluster operations and resource management with Python, cutting infrastructure costs by 30%",
                "Built observability dashboards in Grafana, improving system visibility and reducing incident response time by 40%"
            ]
        },
    ];

    return (
        <div className="flex flex-col items-center space-y-8 p-6 bg-gray-950 text-white max-w-7xl mx-auto">
            
            {/* Avatar */}
            <img src="https://github.com/dizzydoze.png" className="w-32 h-32 rounded-full object-cover" />
            
            {/* Header */}
            <div className="text-center bg-gray-900 p-5 rounded-lg">
                <h1 className="text-3xl font-bold text-cyan-400 mb-2">{header.name}</h1>
                <p className="text-gray-300 text-lg mb-3">{header.title}</p>
                <div className="flex justify-center flex-wrap gap-6 text-sm text-gray-400">
                    {header.contact.map((contact, index) => (
                        <div key={index} className="flex items-center gap-2">
                            {contact.icon}
                            {contact.link ? (
                                <a href={contact.link} className="hover:text-cyan-400 transition-colors">
                                    {contact.text}
                                </a>
                            ) : (
                                <span>{contact.text}</span>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            {/* GitHub Activity */}
            <Repository />

            {/* Resume Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 w-full">
                
                {/* Left Column */}
                <div className="space-y-1.5">
                    
                    {/* Summary */}
                    <div className="bg-gray-900 p-6 rounded-lg">
                        <div className="flex items-center gap-2 mb-3">
                            <User className="w-5 h-5 text-cyan-400" />
                            <h2 className="text-lg font-semibold text-cyan-400">Summary</h2>
                        </div>
                        <p className="text-gray-300 text-sm leading-relaxed">{summary.text}</p>
                    </div>

                    {/* Technical Skills */}
                    <div className="bg-gray-900 p-6 rounded-lg">
                        <div className="flex items-center gap-2 mb-4">
                            <Code className="w-5 h-5 text-cyan-400" />
                            <h2 className="text-lg font-semibold text-cyan-400">Technical Skills</h2>
                        </div>
                        <div className="space-y-3">
                            {Object.entries(techSkills).map(([key, skills]) => (
                                <div key={key}>
                                    <div className="flex items-center gap-1.5 mb-2">
                                        {skillIcons[key]}
                                        <h4 className="text-cyan-300 font-medium text-sm">{skillLabels[key]}</h4>
                                    </div>
                                    <div className="flex flex-wrap gap-1">
                                        {skills.map(skill => (
                                            <span key={skill} className="bg-cyan-900 text-cyan-200 px-2 py-1 rounded text-xs">
                                                {skill}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Education */}
                    <div className="bg-gray-900 p-6 rounded-lg">
                        <div className="flex items-center gap-2 mb-4">
                            <GraduationCap className="w-5 h-5 text-cyan-400" />
                            <h2 className="text-lg font-semibold text-cyan-400">Education</h2>
                        </div>
                        <div className="space-y-4">
                            {education.map((edu, index) => (
                                <div key={index} className={`border-l-3 pl-3 ${edu.current ? 'border-cyan-500' : 'border-gray-600'}`}>
                                    <h3 className="font-medium text-white text-sm">{edu.degree}</h3>
                                    <p className={`text-xs ${edu.current ? 'text-cyan-300' : 'text-gray-400'}`}>{edu.school}</p>
                                    <p className="text-gray-400 text-xs">{edu.period}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Right Column - Experience */}
                <div className="lg:col-span-2 bg-gray-900 p-6 rounded-lg">
                    <div className="flex items-center gap-2 mb-6">
                        <Briefcase className="w-6 h-6 text-cyan-400" />
                        <h2 className="text-xl font-semibold text-cyan-400">Experience</h2>
                    </div>
                    <div className="space-y-6">
                        {experience.map((exp, index) => (
                            <div key={index} className={`border-l-4 pl-4 pb-4 ${exp.current ? 'border-cyan-500' : 'border-gray-600'}`}>
                                <div className="flex justify-between items-start mb-2">
                                    <div>
                                        <h3 className="font-semibold text-white">{exp.title}</h3>
                                        <p className="text-md font-medium text-cyan-300">{exp.company}</p>
                                    </div>
                                    <span className="text-gray-400 text-xs bg-gray-800 px-2 py-1 rounded">{exp.period}</span>
                                </div>
                                <ul className="text-gray-300 text-sm space-y-1 list-disc list-inside">
                                    {exp.achievements.map((achievement, achieveIndex) => (
                                        <li key={achieveIndex}>{achievement}</li>
                                    ))}
                                </ul>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Portfolio;