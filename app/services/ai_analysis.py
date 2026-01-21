import json
import openai
from sqlalchemy import text
from app.extensions import db
from app.models import AIModel, AIChatMessage

class AIAnalysisService:
    def __init__(self, model_id=None):
        if model_id:
            self.model_config = AIModel.query.get(model_id)
        else:
            self.model_config = AIModel.query.filter_by(is_enabled=True).first()
        
        if self.model_config:
            self.client = openai.OpenAI(
                api_key=self.model_config.api_key,
                base_url=self.model_config.api_url
            )
            self.model_name = self.model_config.model_name
        else:
            self.client = None

    def get_database_schema(self):
        # Return a simplified schema for the relevant tables
        return """
        Tables Schema:
        1. users (
            id: Integer (Primary Key), 
            username: String (Unique), 
            nickname: String, 
            email: String (Unique), 
            is_banned: Boolean (0=Normal, 1=Banned), 
            created_at: DateTime
        )
        2. rooms (
            id: Integer (Primary Key), 
            name: String (Unique), 
            description: String, 
            creator_id: Integer (Foreign Key to users.id), 
            created_at: DateTime, 
            is_banned: Boolean (0=Normal, 1=Banned)
        )
        3. messages (
            id: Integer (Primary Key), 
            content: Text, 
            timestamp: DateTime, 
            user_id: Integer (Foreign Key to users.id), 
            room_id: Integer (Foreign Key to rooms.id)
        )
        4. room_members (
            user_id: Integer (Foreign Key to users.id), 
            room_id: Integer (Foreign Key to rooms.id)
        ) - Association table for User-Room Many-to-Many relationship
        5. ws_servers (
            id: Integer (Primary Key), 
            name: String (Unique), 
            address: String, 
            description: String, 
            is_active: Boolean, 
            created_at: DateTime
        )
        6. admin_users (
            id: Integer (Primary Key), 
            username: String (Unique), 
            nickname: String, 
            is_super: Boolean (1=Super Admin), 
            created_at: DateTime
        )
        """

    def execute_sql(self, query):
        # Security check: only allow SELECT
        if not query.strip().upper().startswith('SELECT'):
            return "错误：出于安全原因，仅允许 SELECT 查询。"
        
        try:
            result = db.session.execute(text(query))
            keys = result.keys()
            data = [dict(zip(keys, row)) for row in result.fetchall()]
            # Limit results to avoid token overflow
            if len(data) > 50:
                data = data[:50]
                data.append({"note": "结果已截断至前 50 条"})
            return json.dumps(data, default=str) # Handle datetime serialization
        except Exception as e:
            return f"执行 SQL 错误: {str(e)}"

    def chat_stream(self, messages, session_id=None):
        if not self.client:
            yield json.dumps({"type": "error", "content": "Error: No active AI model configured."}) + "\n"
            return

        # Define tools
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "query_database",
                    "description": "Execute a SQL query to analyze database data. Only SELECT statements are allowed.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The SQL query to execute. e.g. 'SELECT count(*) FROM users'"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]

        # Add system prompt if not present or append schema
        system_message = {
            "role": "system",
            "content": f"""You are a database analysis assistant. You have access to the following database schema:
{self.get_database_schema()}
Use the `query_database` tool to retrieve data when needed. 
Answer in Chinese using Markdown format. 
Always analyze the data returned by the tool to answer the user's question.
If the SQL query fails, try to correct it and run again.
Ensure tables are formatted correctly in Markdown."""
        }
        
        filtered_messages = [m for m in messages if m.get('role') != 'system']
        filtered_messages.insert(0, system_message)

        full_response_content = ""

        try:
            # Yield thinking status
            yield json.dumps({"type": "status", "content": "正在解析用户指令并制定执行计划..."}) + "\n"
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=filtered_messages,
                tools=tools,
                stream=True
            )

            tool_calls = []
            
            for chunk in response:
                delta = chunk.choices[0].delta
                
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        if len(tool_calls) <= tc.index:
                            tool_calls.append({"id": "", "type": "function", "function": {"name": "", "arguments": ""}})
                        
                        tool_call = tool_calls[tc.index]
                        
                        if tc.id:
                            tool_call["id"] = tc.id
                        if tc.function.name:
                            tool_call["function"]["name"] = tc.function.name
                        if tc.function.arguments:
                            tool_call["function"]["arguments"] += tc.function.arguments
                
                if delta.content:
                    content = delta.content
                    full_response_content += content
                    yield json.dumps({"type": "token", "content": content}) + "\n"

            if tool_calls:
                assistant_msg = {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": tool_calls
                }
                filtered_messages.append(assistant_msg)
                
                for tool_call in tool_calls:
                    function_name = tool_call["function"]["name"]
                    arguments = tool_call["function"]["arguments"]
                    
                    if function_name == "query_database":
                        try:
                            args = json.loads(arguments)
                            query = args.get("query")
                            
                            yield json.dumps({"type": "status", "content": f"生成 SQL 查询: {query}"}) + "\n"
                            result = self.execute_sql(query)
                            
                            # Parse result to get count (rough estimate)
                            try:
                                result_data = json.loads(result)
                                row_count = len(result_data) if isinstance(result_data, list) else 0
                                yield json.dumps({"type": "status", "content": f"查询完成，获取到 {row_count} 条数据，正在分析..."}) + "\n"
                            except:
                                yield json.dumps({"type": "status", "content": "数据检索完成，正在分析..."}) + "\n"
                            
                        except Exception as e:
                            result = f"Error parsing arguments: {e}"
                            yield json.dumps({"type": "status", "content": f"参数解析错误: {e}"}) + "\n"
                        
                        filtered_messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": result
                        })

                second_response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=filtered_messages,
                    stream=True
                )
                
                for chunk in second_response:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response_content += content
                        yield json.dumps({"type": "token", "content": content}) + "\n"

            # Save full response to database if session_id is provided
            if session_id and full_response_content:
                try:
                    msg = AIChatMessage(
                        session_id=session_id,
                        role='ai',
                        content=full_response_content
                    )
                    db.session.add(msg)
                    db.session.commit()
                except Exception as e:
                    # Log error but don't break the stream
                    yield json.dumps({"type": "error", "content": f"保存消息错误: {str(e)}"}) + "\n"

        except Exception as e:
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"
