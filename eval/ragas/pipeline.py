import json
import logging
import os
from typing import List, Dict
from agents.graph import app
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from config import get_settings

settings = get_settings()

class Evaluator:
    def __init__(self):
        self.agent = app
        # Judge LLM
        self.judge_llm = ChatOpenAI(
            base_url=settings.OPENAI_BASE_URL,
            api_key=settings.OPENAI_API_KEY,
            model=settings.MODEL_NAME,
            temperature=0
        )
        
    def run_eval(self, dataset_path: str, output_path: str):
        logging.info(f"Loading dataset from {dataset_path}...")
        with open(dataset_path, "r") as f:
            dataset = json.load(f)
            
        results = []
        for item in dataset:
            question = item["question"]
            ground_truth = item["ground_truth"]
            logging.info(f"Evaluating: {question}")
            
            # 1. Run Agent
            initial_state = {"messages": [("user", question)]}
            try:
                final_state = self.agent.invoke(initial_state)
                # Get last AI message
                answer = final_state['messages'][-1].content
            except Exception as e:
                logging.error(f"Agent failed: {e}")
                answer = "Error"
                
            # 2. Judge Code
            score, reason = self._grade_answer(question, ground_truth, answer)
            
            result = {
                "question": question,
                "ground_truth": ground_truth,
                "answer": answer,
                "score": score,
                "reason": reason
            }
            results.append(result)
            
        # 3. Save
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
            
        avg_score = sum(r["score"] for r in results) / len(results) if results else 0
        logging.info(f"Evaluation complete. Average Score: {avg_score:.2f}")

    def _grade_answer(self, question: str, ground_truth: str, answer: str):
        # LLM-as-a-judge
        # Use template variables to safely handle braces in answer
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a teacher grading a student's answer. Compare with ground truth. Score 0 to 1."),
            ("user", """
            Question: {question}
            Ground Truth: {ground_truth}
            Student Answer: {answer}
            
            Return JSON: {{ "score": 0.0 to 1.0, "reason": "short explanation" }}
            """)
        ])
        
        try:
            # Trace Judge with Langfuse if configured
            callbacks = []
            if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
                try:
                    from langfuse.langchain import CallbackHandler
                    langfuse_handler = CallbackHandler(
                        public_key=settings.LANGFUSE_PUBLIC_KEY
                    )
                    callbacks.append(langfuse_handler)
                except ImportError:
                    pass

            chain = prompt | self.judge_llm
            res = chain.invoke({
                "question": question, 
                "ground_truth": ground_truth, 
                "answer": answer
            }, config={"callbacks": callbacks})
            content = res.content
            
            # Clean JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            data = json.loads(content)
            return data.get("score", 0.0), data.get("reason", "No reason")
        except Exception as e:
            logging.warning(f"Grading failed: {e}")
            return 0.0, "Grading Error"

if __name__ == "__main__":
    import sys
    # Simplify logging
    logging.basicConfig(level=logging.INFO)
    
    evaluator = Evaluator()
    evaluator.run_eval("eval/datasets/gold_dataset.json", "artifacts/eval/report.json")
