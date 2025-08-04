import Repository from "./Repository";
import { Globe, Mail, MapPin, User, Code, GraduationCap, Briefcase } from 'lucide-react';

const Portfolio = () => {
    const header = {
        name: "YJ",
        title: "Machine Learning Engineer",
        contact: [
            { icon: <Mail className="w-4 h-4" />, text: "overdosedizzy@gmail.com" },
            { icon: <MapPin className="w-4 h-4" />, text: "San Francisco, CA" }
        ]
    };

    const summary = {
        text: "M.S. Computer Science student with 3+ years software engineering experience specializing in production ML model fine-tuning using PyTorch, multi-agent platforms using LangChain/LangGraph, and full-stack AI application deployment."
    };

    const techSkills = {
        languages: ['Python', 'Java', 'JavaScript', 'TypeScript', 'Golang', 'SQL'],
        aiml: ['PyTorch', 'LangChain', 'RAG', 'LLM fine-tuning', 'TensorFlow', 'CNNs'],
        frameworks: ['React', 'FastAPI', 'Flask', 'Django', 'Docker', 'AWS']
    };

    const education = [
        {
            degree: "M.S. Computer Science",
            school: "University of San Francisco",
            period: "Aug 2023 – Present",
            current: true
        },
    ];

    const experience = [
        {
            title: "Machine Learning Engineer Intern",
            company: "LenderToolkit",
            period: "May 2025 – Present",
            current: true,
            achievements: [
                "Architected multi-agent mortgage automation platform using FastAPI and LangChain/LangGraph framework",
                "Implemented RAG pipeline with PostgreSQL for mortgage guideline embeddings using cosine similarity search",
                "Modified LibreChat open-source frontend by developing custom RAG tools in the backend",
                "Deployed scalable infrastructure using Docker containerization and AWS ECS with Registry integration"
            ]
        },
        {
            title: "Full Stack Software Engineer Intern",
            company: "ValueGlance",
            period: "Feb 2025 – May 2025",
            current: false,
            achievements: [
                "Built core features for financial analytics platform using React, JavaScript/TypeScript, and Vite",
                "Implemented RESTful APIs with Flask and utilized Docker for packaging and deployment",
                "Automated CI/CD pipelines and leveraged AWS services (EC2, S3, Lambda, API Gateway)"
            ]
        },
        {
            title: "Teaching Assistant of AI Foundation",
            company: "University of San Francisco",
            period: "Aug 2024 – May 2025",
            current: false,
            achievements: [
                "Supported instruction in core AI topics: search, optimization, Decision Trees, KNN, probabilistic inference",
                "Guided students through coding assignments, lab exercises, and problem-solving sessions"
            ]
        },
        {
            title: "Software Engineer",
            company: "OPPO",
            period: "Mar 2019 – Oct 2020",
            current: false,
            achievements: [
                "Developed backend services using Flask and Django, designed APIs for Data Analysis Department",
                "Developed migration platform facilitating successful migration of 100 PB of data across 20+ clusters",
                "Automated cluster management using Python, improving efficiency by 30%"
            ]
        }
    ];

    return (
        <div className="flex flex-col items-center space-y-8 p-6 bg-gray-950 text-white max-w-7xl mx-auto">
            
            {/* Avatar */}
            <img src="/assets/avatar.jpeg" className="w-32 h-32 rounded-full object-cover" />
            
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
                            <div>
                                <h4 className="text-cyan-300 font-medium text-sm mb-2">Languages</h4>
                                <div className="flex flex-wrap gap-1">
                                    {techSkills.languages.map(skill => (
                                        <span key={skill} className="bg-cyan-900 text-cyan-200 px-2 py-1 rounded text-xs">
                                            {skill}
                                        </span>
                                    ))}
                                </div>
                            </div>
                            <div>
                                <h4 className="text-cyan-300 font-medium text-sm mb-2">AI/ML</h4>
                                <div className="flex flex-wrap gap-1">
                                    {techSkills.aiml.map(skill => (
                                        <span key={skill} className="bg-cyan-900 text-cyan-200 px-2 py-1 rounded text-xs">
                                            {skill}
                                        </span>
                                    ))}
                                </div>
                            </div>
                            <div>
                                <h4 className="text-cyan-300 font-medium text-sm mb-2">Frameworks</h4>
                                <div className="flex flex-wrap gap-1">
                                    {techSkills.frameworks.map(skill => (
                                        <span key={skill} className="bg-cyan-900 text-cyan-200 px-2 py-1 rounded text-xs">
                                            {skill}
                                        </span>
                                    ))}
                                </div>
                            </div>
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
                        {/* Highlight the most recent one */}
                        {experience.map((exp, index) => (
                            <div key={index} className={`border-l-4 pl-4 pb-4 ${index < 0 ? 'border-b border-gray-800' : ''} ${exp.current ? 'border-cyan-500' : 'border-gray-600'}`}>
                                <div className="flex justify-between items-start mb-2">
                                    <div>
                                        <h3 className="font-semibold text-white">{exp.title}</h3>
                                        <p className={'text-sm font-medium text-cyan-300'}>{exp.company}</p>
                                    </div>
                                    <span className="text-gray-400 text-xs bg-gray-800 px-2 py-1 rounded">{exp.period}</span>
                                </div>
                                <ul className="text-gray-300 text-xs space-y-1 list-disc list-inside">
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