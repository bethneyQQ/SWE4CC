#!/usr/bin/env python3
"""
Enhanced prompts that guide Claude Code to use its tools
"""
from typing import Dict


def prepare_enhanced_claude_code_prompt(datum: Dict, repo_path: str) -> str:
    """
    Create a prompt that explicitly guides Claude Code to use its tools.

    This is the KEY difference from direct API calls - we tell Claude Code
    it can and should use tools to access the actual codebase.
    """
    instance_id = datum.get("instance_id", "unknown")
    problem = datum.get("problem_statement", "")
    hints = datum.get("hints_text", "")
    base_commit = datum.get("base_commit", "")

    prompt = f"""You are debugging issue {instance_id} in a git repository.

**REPOSITORY INFO:**
- Path: {repo_path}
- Commit: {base_commit}
- You have full access to read files using the Read tool
- You can search code using Grep tool
- You can run commands using Bash tool

**PROBLEM DESCRIPTION:**
{problem}

**HINTS (files that may be relevant):**
{hints if hints else "No specific hints provided - you'll need to explore the codebase"}

**YOUR TASK:**
Generate a patch to fix this issue. You MUST use your tools to ensure accuracy:

**STEP 1: EXPLORE THE CODEBASE**
- Use Bash to navigate to {repo_path}
- Use Grep or Bash (find, grep) to locate relevant files
- Use Read to examine the actual code at this commit

**STEP 2: ANALYZE THE ISSUE**
- Read the actual file contents (don't guess!)
- Identify the exact location that needs to be changed
- Note the EXACT line numbers from the real file

**STEP 3: GENERATE ACCURATE PATCH**
- Create a unified diff patch
- Use EXACT line numbers from the files you just read
- Include 3+ lines of context before and after changes
- Ensure context lines start with a SPACE character

**STEP 4: VERIFY YOUR PATCH**
- Double-check line numbers match the actual file
- Verify context lines are exact matches
- Ensure the patch ends with a newline

**CRITICAL RULES:**
1. ✅ READ files before generating patches - don't guess content or line numbers
2. ✅ Use exact line numbers from the actual files you read
3. ✅ Context lines MUST start with a space ` `
4. ✅ Show complete functions/blocks when possible
5. ✅ Patch must end with a newline character

**OUTPUT FORMAT:**
Provide:
1. Brief analysis (1-2 sentences)
2. Your patch in a ```diff``` code block

Example of CORRECT patch format:
```diff
--- a/path/to/file.py
+++ b/path/to/file.py
@@ -10,6 +10,7 @@
 def function():
     existing_line = True
     if condition:
-        old_code()
+        new_code()
+        additional_line()
     return result
```

Remember: You have tools! Use Read to see the actual code before generating the patch."""

    return prompt


def prepare_retry_prompt(original_prompt: str, validation_error: str, attempt: int) -> str:
    """
    Create a retry prompt with specific error feedback
    """
    return f"""{original_prompt}

---

**⚠️ RETRY ATTEMPT {attempt}**

Your previous patch had validation errors:
```
{validation_error}
```

**Common issues to fix:**
- Line numbers don't match actual file (use Read to verify!)
- Context lines missing leading space
- Hunk boundaries incorrect
- File path wrong

Please generate a CORRECTED patch using the Read tool to verify all line numbers."""


def prepare_tool_guidance_prompt(datum: Dict) -> str:
    """
    Simpler prompt that emphasizes tool usage
    """
    problem = datum.get("problem_statement", "")
    hints = datum.get("hints_text", "")

    return f"""**Problem:** {problem}

**Files to check:** {hints if hints else "Search for relevant files"}

**Instructions:**
1. Use Bash/Grep to find relevant files
2. Use Read to examine the code
3. Generate a patch with accurate line numbers from the actual files

Start by exploring the codebase."""
