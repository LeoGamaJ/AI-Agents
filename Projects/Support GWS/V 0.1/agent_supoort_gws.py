from typing import Dict
from datetime import datetime
import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

class GoogleWorkspaceCrewAI:
    def __init__(self, output_dir: str = "support_responses"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize OpenAI
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key não encontrada. Por favor, configure-a no arquivo .env")
        
        self.llm = ChatOpenAI(
            temperature=0.2,
            model_name="gpt-4o-mini",
            max_tokens=3000
        )

    def create_agents(self) -> Dict[str, Agent]:
        """Create specialized support agents"""
        
        analyst_agent = Agent(
            role='Support Analyst',
            goal='Analyze and classify Google Workspace support requests',
            backstory="""You are a skilled support analyst specializing in Google Workspace.
            Your role is to analyze support requests, classify their severity, and provide
            initial assessment. Communicate in English for precise technical terms.""",
            verbose=True,
            allow_delegation=True,
            llm=self.llm
        )

        tech_agent = Agent(
            role='Technical Support Engineer',
            goal='Provide technical solutions for Google Workspace issues',
            backstory="""You are an experienced technical support engineer with deep
            knowledge of Google Workspace. You provide detailed solutions and
            step-by-step guides. Use English for technical accuracy.""",
            verbose=True,
            allow_delegation=True,
            llm=self.llm
        )

        expert_agent = Agent(
            role='Workspace Expert',
            goal='Handle complex issues and provide expert guidance',
            backstory="""You are a Google Workspace expert with extensive knowledge
            of enterprise implementations, security, and advanced features.
            Communicate in English for consistency with Google documentation.""",
            verbose=True,
            allow_delegation=True,
            llm=self.llm
        )

        translator_agent = Agent(
            role='Brazilian Portuguese Translator',
            goal='Translate technical support responses to Brazilian Portuguese',
            backstory="""You are a specialized technical translator with expertise in 
            translating IT and cloud computing content to Brazilian Portuguese (pt-BR). 
            You maintain technical accuracy while ensuring the language is natural and 
            appropriate for Brazilian users. You keep technical terms that are commonly 
            used in English in the IT field.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

        return {
            "analyst": analyst_agent,
            "tech": tech_agent,
            "expert": expert_agent,
            "translator": translator_agent
        }

    def create_tasks(self, user_input: str, agents: Dict[str, Agent]) -> list[Task]:
        """Create tasks for handling the support request"""
        
        analysis_task = Task(
            description=f"""Analyze the following Google Workspace support request:
            
            {user_input}
            
            1. Classify the severity (Low/Medium/High)
            2. Identify the specific Google Workspace service involved
            3. List any potential security implications
            4. Determine if this requires escalation
            
            Provide a structured analysis with these points.""",
            agent=agents["analyst"],
            expected_output="A detailed analysis of the support request with classification and recommendations"
        )

        solution_task = Task(
            description=f"""Based on the analysis, provide a solution for:
            
            {user_input}
            
            Include:
            1. Step-by-step resolution steps
            2. Required permissions or access levels
            3. Best practices and recommendations
            4. Prevention tips for similar issues
            
            Format as a clear support response.""",
            agent=agents["tech"],
            expected_output="A comprehensive solution with clear steps and recommendations"
        )

        review_task = Task(
            description=f"""Review the solution for the following issue:
            
            {user_input}
            
            1. Verify technical accuracy
            2. Add any missing enterprise considerations
            3. Include relevant Google Workspace updates or features
            4. Provide additional security recommendations
            
            Enhance the solution if needed.""",
            agent=agents["expert"],
            expected_output="Expert review and enhancement of the solution"
        )

        translation_task = Task(
            description=f"""Translate the following technical support response to Brazilian Portuguese (pt-BR):
            
            [Previous Analysis and Solution will be here]
            
            Guidelines:
            1. Maintain technical accuracy
            2. Use natural Brazilian Portuguese
            3. Keep common technical terms in English (e.g., "login", "backup", "dashboard")
            4. Adapt any cultural references or examples for Brazilian context
            5. Use formal but friendly tone appropriate for professional communication
            6. Format the response clearly with proper sections
            
            Ensure the translation is clear and professional while maintaining technical precision.""",
            agent=agents["translator"],
            expected_output="A professional Brazilian Portuguese translation of the support response"
        )

        return [analysis_task, solution_task, review_task, translation_task]

    def save_response(self, user_input: str, response: str) -> str:
        """Save the support response to a file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sanitized_input = "".join(x for x in user_input[:30] if x.isalnum() or x.isspace()).strip()
        sanitized_input = sanitized_input.replace(" ", "_")
        
        filename = f"{timestamp}_{sanitized_input}.txt"
        filepath = os.path.join(self.output_dir, filename)
        
        content = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "response": str(response)
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("=== Resposta do Suporte Google Workspace ===\n\n")
            f.write(f"Data/Hora: {content['timestamp']}\n")
            f.write(f"Solicitação: {content['user_input']}\n")
            f.write("\n=== Resposta ===\n")
            f.write(content['response'])
        
        return filepath

    def process_request(self, user_input: str) -> str:
        """Process a support request using the CrewAI framework"""
        try:
            # Create agents and tasks
            agents = self.create_agents()
            tasks = self.create_tasks(user_input, agents)
            
            # Create and configure the crew
            crew = Crew(
                agents=list(agents.values()),
                tasks=tasks,
                verbose=True,
                process=Process.sequential
            )
            
            # Execute the support process
            result = crew.kickoff()
            
            # Save the response
            filepath = self.save_response(user_input, result)
            
            return f"{str(result)}\n\nResposta salva em: {filepath}"
            
        except Exception as e:
            error_msg = f"Erro ao processar solicitação: {str(e)}"
            filepath = self.save_response(user_input, error_msg)
            return f"{error_msg}\n\nLog de erro salvo em: {filepath}"

def display_banner():
    """Display a beautiful ASCII art banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   🤖 Agent Support GWS - Google Workspace Support Assistant   ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def display_menu():
    """Display the main menu options"""
    menu = """
    🔍 Choose an option:
    
    1. Submit support request
    2. View last response
    3. Help
    4. Exit
    """
    print(menu)

def display_help():
    """Display help information"""
    help_text = """
    📚 Help Guide
    ============
    
    This assistant can help you with various Google Workspace issues, such as:
    
    • Email configuration and troubleshooting
    • Account security and 2FA
    • Domain and DNS settings
    • User management
    • Access and permissions
    • Google Workspace features
    ...
    
    Tips for best results:
    ---------------------
    1. Be specific in your request
    2. Include relevant details
    3. Mention any error messages
    4. Specify the affected service
    
    All responses are saved in the 'support_responses' directory.
    
    Press Enter to return to main menu...
    """
    print(help_text)
    input()

def display_processing_animation():
    """Display a simple processing animation"""
    import sys
    import time
    
    animation = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    for i in range(10):
        for char in animation:
            sys.stdout.write(f"\r🔄 Processing request... {char}")
            sys.stdout.flush()
            time.sleep(0.1)

def main():
    """Main function to run the support system"""
    support_system = GoogleWorkspaceCrewAI()
    
    display_banner()
    print("\n🌟 Welcome to Google Workspace Support Assistant!")
    
    while True:
        display_menu()
        choice = input("\n👉 Enter your choice (1-4): ").strip()
        
        if choice == "1":
            print("\n📝 Submit your support request")
            print("--------------------------------")
            print("Tip: Be specific and include relevant details")
            user_input = input("\n🔍 Describe your issue: ")
            
            if user_input.strip():
                print("\n🔄 Processing your request...")
                display_processing_animation()
                
                response = support_system.process_request(user_input)
                
                print("\n✨ Support Response:")
                print("------------------")
                print(response)
                
                input("\nPress Enter to continue...")
            
        elif choice == "2":
            # List the most recent response file
            try:
                responses_dir = "support_responses"
                files = sorted([f for f in os.listdir(responses_dir) if f.endswith('.txt')],
                             key=lambda x: os.path.getctime(os.path.join(responses_dir, x)),
                             reverse=True)
                
                if files:
                    latest_file = os.path.join(responses_dir, files[0])
                    print(f"\n📄 Latest Response ({files[0]}):")
                    print("-" * 50)
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        print(f.read())
                else:
                    print("\n❌ No previous responses found.")
                
                input("\nPress Enter to continue...")
            
            except Exception as e:
                print(f"\n❌ Error reading response file: {str(e)}")
                input("\nPress Enter to continue...")
        
        elif choice == "3":
            display_help()
        
        elif choice == "4":
            print("\n👋 Thank you for using Google Workspace Support Assistant!")
            print("Have a great day! 🌟\n")
            break
        
        else:
            print("\n❌ Invalid option. Please choose 1-4.")
            input("Press Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Program terminated by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")
        print("Please check your configuration and try again.")