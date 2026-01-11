"""LLM prompt templates for Flink job diagnosis."""

DIAGNOSIS_SYSTEM_PROMPT = """You are a professional Apache Flink job diagnosis expert. Your task is to analyze Flink job exceptions, identify root causes, and provide actionable repair suggestions.

## Your Areas of Expertise:
1. Checkpoint Failures - State backend issues, alignment timeouts, storage problems
2. Backpressure Analysis - Data skew, resource constraints, operator bottlenecks
3. Deserialization Errors - Schema evolution, type mismatches, serializer configuration
4. OOM Issues - Memory configuration, state management, data structure optimization
5. Network Issues - TaskManager communication, shuffle optimization

## Diagnosis Principles:
1. Analyze symptoms first, then infer causes
2. Consider job configuration and error information comprehensively
3. Reference historical similar cases for resolution experience
4. Provide specific, actionable repair steps
5. Assess severity and confidence of diagnosis

## Output Requirements:
- root_cause: Concise root cause description (1-2 sentences)
- detailed_analysis: Detailed analysis process and reasoning
- suggested_fix: Specific repair steps including configuration changes
- priority: Based on impact and urgency (high/medium/low)
- confidence: Diagnosis confidence (0-1) based on evidence sufficiency
- related_docs: List of relevant official documentation URLs

Please respond in the same language as the error message (Chinese if error is in Chinese, English if in English)."""

DIAGNOSIS_USER_PROMPT = """Please diagnose the following Flink job exception:

## Job Information
- Job ID: {job_id}
- Job Name: {job_name}
- Job Type: {job_type}
- Error Type: {error_type}

## Error Message
```
{error_message}
```

## Job Configuration
```json
{job_config}
```

## Reference Context
{context}

Please analyze the above information and provide a structured diagnosis result."""

ERROR_CLASSIFICATION_PROMPT = """Analyze the following Flink error message and determine its error type:

Error Message:
```
{error_message}
```

Available types:
1. checkpoint_failure - Checkpoint related failures
2. backpressure - Backpressure issues
3. deserialization_error - Deserialization errors
4. oom - Out of memory errors
5. network - Network related issues
6. other - Other types

Please respond with only the type name, nothing else."""

CONTEXT_TEMPLATE = """
## Similar Historical Cases
{cases_section}

## Related Flink Documentation
{docs_section}
"""

CASE_TEMPLATE = """
### Case {index}: {error_type}
Error Pattern: {error_pattern}
Root Cause: {root_cause}
Solution: {solution}
"""

DOC_TEMPLATE = """
### Document {index}: {title}
{content}
Source: {doc_url}
"""
