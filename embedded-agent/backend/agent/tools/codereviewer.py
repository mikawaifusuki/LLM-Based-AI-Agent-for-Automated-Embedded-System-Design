import os
import json
import logging
from typing import List, Dict, Any, Optional

from langchain.tools.base import BaseTool
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain.chains import RetrievalQA
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('embedded_agent.codereviewer')

class CodeReviewTool(BaseTool):
    """用于对C语言代码进行智能审查的工具。
    
    该工具在SDCC编译前执行，分析代码中可能存在的格式、结构、安全或性能问题，
    并提供优化建议。使用基于向量检索的问答系统，从知识库中提取相关的最佳实践。
    """

    name: str = "CodeReviewTool"
    description: str = """
    在代码编译前对C语言代码进行智能审查，识别潜在问题并提供改进建议。
    输入：C语言代码字符串
    输出：审查建议
    """
    
    knowledge_path: str = "docs/code_review_knowledge.jsonl"
    embedding_model: str = "text-embedding-3-small"
    qa_model: str = "o4-mini"
    retrieval_qa: Any = None
    is_fully_initialized: bool = False
    
    def __init__(
        self, 
        knowledge_path: Optional[str] = None,
        embedding_model: Optional[str] = None,
        qa_model: Optional[str] = None
    ):
        """初始化代码审查工具。
        
        Args:
            knowledge_path: 知识库JSONL文件路径
            embedding_model: 使用的嵌入模型名称
            qa_model: 使用的问答模型名称
        """
        super().__init__()
        
        if knowledge_path:
            self.knowledge_path = knowledge_path
        if embedding_model:
            self.embedding_model = embedding_model
        if qa_model:
            self.qa_model = qa_model
            
        # 尝试获取绝对路径
        self._resolve_knowledge_path()
            
        # 初始化检索问答链（用try-except包装确保不会因初始化失败而阻止Agent启动）
        try:
            self.retrieval_qa = self._init_retrieval_qa()
            self.is_fully_initialized = True
        except Exception as e:
            logger.error(f"代码审查工具初始化失败，将使用基本模式: {str(e)}")
            self.is_fully_initialized = False
            self.retrieval_qa = None
    
    def _resolve_knowledge_path(self):
        """解析知识库路径，尝试找到文件的绝对路径"""
        # 当前路径
        current_path = self.knowledge_path
        
        # 如果是相对路径，尝试不同的基础目录
        if not os.path.isabs(current_path):
            # 尝试方案1：相对于当前工作目录
            if os.path.exists(current_path):
                self.knowledge_path = os.path.abspath(current_path)
                logger.info(f"找到知识库文件: {self.knowledge_path}")
                return
                
            # 尝试方案2：相对于项目根目录
            try:
                # 推测项目根目录（向上查找backend目录）
                current_dir = os.path.dirname(os.path.abspath(__file__))  # tools目录
                agent_dir = os.path.dirname(current_dir)  # agent目录
                backend_dir = os.path.dirname(agent_dir)  # backend目录
                project_root = os.path.dirname(backend_dir)  # 项目根目录
                
                root_based_path = os.path.join(project_root, self.knowledge_path)
                if os.path.exists(root_based_path):
                    self.knowledge_path = root_based_path
                    logger.info(f"找到知识库文件: {self.knowledge_path}")
                    return
            except Exception as e:
                logger.warning(f"尝试推测项目根目录时出错: {str(e)}")
                
            # 路径可能有效，但文件不存在，将在加载时处理
            logger.warning(f"无法找到知识库文件: {current_path}")
        
    def _load_knowledge(self) -> List[Document]:
        """从JSONL文件加载知识库数据。"""
        documents = []
        try:
            logger.info(f"从 {self.knowledge_path} 加载知识库")
            
            if not os.path.exists(self.knowledge_path):
                logger.error(f"知识库文件不存在: {self.knowledge_path}")
                # 如果没有知识库文件，创建内置的默认知识
                documents = self._create_default_knowledge()
                return documents
                
            with open(self.knowledge_path, 'r', encoding='utf-8') as file:
                for line in file:
                    try:
                        data = json.loads(line.strip())
                        if "content" in data:
                            documents.append(Document(
                                page_content=data["content"],
                                metadata={"source": self.knowledge_path}
                            ))
                    except json.JSONDecodeError:
                        logger.warning(f"无法解析JSONL行: {line}")
                        continue
                        
            logger.info(f"成功加载 {len(documents)} 条知识库记录")
            
            # 如果没有加载到任何记录，使用默认知识
            if not documents:
                documents = self._create_default_knowledge()
            
        except Exception as e:
            logger.error(f"加载知识库时出错: {str(e)}")
            # 使用默认知识
            documents = self._create_default_knowledge()
            
        return documents
    
    def _create_default_knowledge(self) -> List[Document]:
        """创建默认的内置知识库，当无法加载外部知识库时使用"""
        logger.info("创建默认的嵌入式代码最佳实践知识库")
        
        default_knowledge = [
            "在C语言中，所有变量应在使用前声明和初始化，避免未初始化导致的不确定行为。",
            "避免使用gets()、strcpy()等不安全的函数，它们容易导致缓冲区溢出。使用fgets()、strncpy()替代，并总是指定缓冲区大小。",
            "在8051单片机编程中，使用P0、P1、P2、P3等宏定义访问端口，而不是直接使用地址。这样能提高代码可读性和可移植性。",
            "在嵌入式系统中，避免使用动态内存分配（如malloc/free），因为内存碎片和内存泄漏问题难以追踪和修复。",
            "使用volatile关键字修饰与硬件通信或被中断修改的变量，防止编译器优化导致的问题。",
            "在C语言中，数组索引从0开始，长度为n的数组，最大有效索引为n-1。访问超出边界的内存可能导致未定义行为。"
        ]
        
        documents = []
        for knowledge in default_knowledge:
            documents.append(Document(
                page_content=knowledge,
                metadata={"source": "default_embedded_knowledge"}
            ))
            
        return documents
        
    def _init_retrieval_qa(self) -> Optional[RetrievalQA]:
        """初始化检索问答链。"""
        try:
            # 加载知识库文档
            documents = self._load_knowledge()
            
            # 文本分割器
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=100,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            
            # 分割文档
            split_docs = text_splitter.split_documents(documents)
            
            # 创建嵌入模型
            try:
                embeddings = OpenAIEmbeddings(model=self.embedding_model)
            except Exception as e:
                logger.error(f"创建嵌入模型时出错: {str(e)}")
                raise RuntimeError(f"无法创建OpenAI嵌入模型，请检查API密钥和连接: {str(e)}")
            
            # 创建向量存储
            vector_store = FAISS.from_documents(split_docs, embeddings)
            
            # 创建检索器
            retriever = vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}  # 检索5条最相关的知识
            )
            
            # 创建大语言模型
            try:
                llm = ChatOpenAI(model_name=self.qa_model, temperature=0)
            except Exception as e:
                logger.error(f"创建ChatOpenAI模型时出错: {str(e)}")
                raise RuntimeError(f"无法创建ChatOpenAI模型，请检查API密钥和连接: {str(e)}")
            
            # 创建检索问答链
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True,
                chain_type_kwargs={
                    "prompt": self._get_review_prompt()
                }
            )
            
            logger.info("成功初始化代码审查问答链")
            return qa_chain
            
        except Exception as e:
            logger.error(f"初始化问答链时出错: {str(e)}")
            return None
            
    def _get_review_prompt(self) -> PromptTemplate:
        """获取代码审查提示模板。"""
        template = """你是资深嵌入式系统代码审查专家，特别擅长8051系列单片机编程。
请对下面的C语言代码进行全面审查，识别可能存在的以下问题：

1. 语法错误和编译隐患
2. 命名和代码风格问题
3. 安全性隐患（如缓冲区溢出、未初始化变量等）
4. 性能问题（尤其是在资源受限的嵌入式环境中）
5. 可读性和可维护性问题
6. 嵌入式系统常见陷阱（如中断处理、I/O操作等）

使用以下相关知识帮助你进行审查：
{context}

审查的代码：
```c
{question}
```

请提供详细的审查报告，包括：
1. 严重问题（可能导致编译错误或运行时错误的问题）
2. 警告（不会导致程序失败但应改进的问题）
3. 建议（针对代码质量、风格和最佳实践的改进建议）

针对每个问题，请明确指出问题所在行或代码片段，问题的具体原因，以及修改建议。
"""
        return PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )

    def _perform_basic_review(self, code: str) -> str:
        """当高级审查失败时执行的基本代码审查。
        
        这个方法不依赖外部API，提供最基本的代码检查。
        """
        logger.info("执行基本代码审查")
        
        issues = []
        suggestions = []
        
        # 检查未初始化变量
        if "int " in code and "=" not in code.split("int ")[1].split(";")[0]:
            issues.append("发现可能的未初始化变量。建议在声明变量时进行初始化。")
            
        # 检查安全函数使用
        if "gets(" in code:
            issues.append("使用了不安全的gets()函数，存在缓冲区溢出风险。建议使用fgets()替代，并指定缓冲区大小。")
            
        # 检查volatile关键字
        if ("P0" in code or "P1" in code or "P2" in code or "P3" in code) and "volatile" not in code:
            suggestions.append("代码访问了I/O端口但未使用volatile关键字。对于与硬件交互的变量，建议使用volatile修饰。")
            
        # 检查延时函数
        if "delay" in code and "unsigned" not in code:
            suggestions.append("代码中使用了延时函数，但可能没有使用unsigned类型。在计时功能中使用signed类型可能导致整数溢出问题。")
        
        # 生成审查报告
        if not issues and not suggestions:
            return "基本代码审查未发现明显问题。由于完整审查服务不可用，建议手动检查代码质量和安全性。"
            
        report = "基本代码审查报告（受限模式）：\n\n"
        
        if issues:
            report += "问题：\n"
            for issue in issues:
                report += f"- {issue}\n"
            report += "\n"
            
        if suggestions:
            report += "建议：\n"
            for suggestion in suggestions:
                report += f"- {suggestion}\n"
                
        report += "\n注意：这是一个基本审查报告，完整的代码审查服务当前不可用。"
        return report

    def _run(self, code: str) -> str:
        """执行代码审查。

        Args:
            code: 要审查的C语言代码

        Returns:
            包含审查建议的字符串
        """
        try:
            logger.info("开始执行代码审查")
            
            if not code or len(code.strip()) == 0:
                return "无代码提供，无法进行审查。请提供有效的C语言代码。"
            
            # 检查是否完全初始化
            if not self.is_fully_initialized or self.retrieval_qa is None:
                logger.warning("使用基本审查模式，因为高级审查模式不可用")
                return self._perform_basic_review(code)
                
            # 使用检索问答链进行代码审查
            try:
                result = self.retrieval_qa({"query": code})
                review_result = result["result"]
                
                # 提取使用的知识条目（可选，用于调试）
                source_docs = result.get("source_documents", [])
                sources = [doc.page_content for doc in source_docs]
                
                logger.info(f"代码审查完成，使用了 {len(sources)} 条相关知识")
                
                return review_result
            except Exception as e:
                logger.error(f"使用检索问答链审查代码时出错: {str(e)}")
                return self._perform_basic_review(code)
            
        except Exception as e:
            error_msg = f"代码审查过程中出错: {str(e)}"
            logger.error(error_msg)
            return f"审查失败: {error_msg}\n\n建议手动检查代码，特别注意变量初始化、缓冲区溢出和资源管理问题。"
            
    def _tool_run(self, code: str) -> str:
        """工具运行接口，调用_run方法执行代码审查。"""
        return self._run(code)

# 便捷函数，用于直接调用代码审查
def review_code(code: str) -> str:
    """对C语言代码进行代码审查。
    
    Args:
        code: 要审查的C语言代码
        
    Returns:
        包含审查建议的字符串
    """
    try:
        reviewer = CodeReviewTool()
        return reviewer._tool_run(code)
    except Exception as e:
        logging.error(f"执行代码审查时发生错误: {str(e)}")
        return f"无法完成代码审查，原因: {str(e)}\n\n建议手动检查代码质量和安全性。"
    
if __name__ == "__main__":
    # 测试示例
    test_code = """
    #include <8051.h>
    
    void main() {
        int i;
        P1 = 0;
        while(1) {
            for(i=0; i<1000; i++);
            P1 = ~P1;
        }
    }
    """
    
    result = review_code(test_code)
    print(result) 