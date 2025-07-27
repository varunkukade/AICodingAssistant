analyse_feedback_prompt = [
    (
        "system",
        """
            You will receive:
            1. A list of files, each with its filename, whether file exists or not - boolean value, and full content. 

            File Data:
            {formatted_files}

            User has asked to:
            1. Analyse files
            2. Edit/refactor/update files
            3. Analyse and edit files

            Based on user query, we already identified the files to be analysed and edited.
            While doing this we found that one or more file was found at different paths.
            Hence asked user to confirm the file paths. Here is what we prompted user:

            ### `file_path_confirmation_prompt`:
            {file_path_confirmation_prompt}

            Then user responded with natural language text. Here is user's response:

            ### `human_feedback`:
            {human_feedback}

            Your Role:
            Your task is to analyse the human feedback and return updated files.


            Return your output as follows:
            {{
                "files": [
                    {{
                        "file_name": "filename.py",
                        "content": "always return empty string for now",
                        "file_path": "file path here",
                        "exists": always return true
                    }}
                ],
                "additional_query": "Decoded additional user intent here if any",
                "should_end": "Provide true if you are ending the flow, else false",
                "summary": "Provide only if you are ending the flow"
            }}

            ---

            ### For constructing each file object, refer to this logic:
            'human_feedback' can either contain just the confirmation of file paths as per `file_path_confirmation_prompt` 
            Or it can also contain additional queries by user.
            Please note: To decide if user is providing additional file queries or not, strictly use 'human_feedback' and not 'file_path_confirmation_prompt'.

            
            Now based on 'human_feedback' one or more of the following scenarios can occur:

            1. **Valid Path Confirmation**  
            Human can respond with valid file paths for the given files in natural language.
            → Your task is to match those paths correctly to each file name.  
            → For each file, return an object with:
            - `file_name`: confirmed file name  
            - `file_path`: path confirmed by the user  
            - `content`: always return empty string for now  
            - `exists`: always return `true` for now  
            Here don't return any additional_query.

            2. **Valid Paths + Additional File Queries:**  
            Human can respond with valid paths as above and also mention additional file(s) in their query asking for refactor/edit/analysis.  
            → In this case, follow scenario 1 for the confirmed and valid paths.
            → Also extract additional query as a single natural language string and pass it to `additional_query`. To extract this strictly use 'human_feedback'.
            - If you don't find any additional query in 'human_feedback', consider this as 1st (**Valid Path Confirmation and No Additional queries:**) path and don't return additional_query.

            3. **Invalid Paths:** - End the flow 
            Human can respond with paths that are not present in the original `file_path_confirmation_prompt` or it can only contain additional queries without any valid paths. 
            → In this case, we assume the input is invalid and terminate the flow.  
            → Return an empty `files` list, empty `additional_query`, and set `should_end` to `true`.
            - Inside `summary` provide a clear and easy to understand descriptive summary on why the flow is ending.
            """,
    ),
]
