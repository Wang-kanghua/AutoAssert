import pandas as pd
import re
import os


ASSERTION_CATEGORIES = {
    'immediate': [
        r'immediate\s+assert', r'assert\s+immediate', r'assert\s*\(\s*.*\s*\)\s*;',
        r'cover\s*\(\s*.*\s*\)\s*;', r'assume\s*\(\s*.*\s*\)\s*;'
    ],
    'concurrent': [
        r'assert\s+property', r'cover\s+property', r'assume\s+property',
        r'assert\s+final', r'cover\s+final', r'assume\s+final',
        r'@\s*\(\s*posedge|negedge', r'always\s+@', r'always_comb|always_ff|always_latch'
    ],
    'temporal': [
        r'##\d+', r'\[\s*\d+\s*:\s*\d+\s*\]', r'within|throughout|until|before|after',
        r'##\[', r'##\*', r'->', r'|=>', r'overlap|non-overlap',
        r'first_match', r'not\s*\(\s*.*\s*\)', r'and|or|intersect'
    ],
    'functional': [
        r'onehot', r'onehot0', r'zeroone', r'range', r'stable',
        r'changed', r'rose|fell|stable', r'past', r'prev',
        r'unique|unique0', r'countones', r'isunknown'
    ]
}


COMMENT_PATTERNS = [
    r'//.*assert', r'/\*.*assert.*\*/', r'//.*cover', r'/\*.*cover.*\*/',
    r'//.*assume', r'/\*.*assume.*\*/', r'#.*assert', r'#.*cover', r'#.*assume'
]

def classify_assertion(assertion_code):

    code_lower = assertion_code.lower().strip()
    
    for category, patterns in ASSERTION_CATEGORIES.items():
        for pattern in patterns:
            if re.search(pattern, code_lower, re.IGNORECASE):
                return category
    

    if any(keyword in code_lower for keyword in ['property', 'sequence']):
        return 'concurrent'
    elif any(keyword in code_lower for keyword in ['immediate', 'assert(']):
        return 'immediate'
    elif any(keyword in code_lower for keyword in ['##', '->', '|=>']):
        return 'temporal'
    else:
        return 'unknown'

def check_assertion_comment(file_path, line_number, assertion_code):

    try:
        if not os.path.exists(file_path):
            return "file_not_found"
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        line_idx = line_number - 1          
        if line_idx < 0 or line_idx >= len(lines):
            return "line_not_found"
        

        current_line = lines[line_idx].strip()
        if re.search(r'//|/\*|#', current_line):
            for pattern in COMMENT_PATTERNS:
                if re.search(pattern, current_line, re.IGNORECASE):
                    return "has_comment"
        

        if line_idx > 0:
            prev_line = lines[line_idx - 1].strip()
            if any(re.search(pattern, prev_line, re.IGNORECASE) for pattern in COMMENT_PATTERNS):
                return "has_comment"
        

        if line_idx > 1:
            prev_prev_line = lines[line_idx - 2].strip()
            if any(re.search(pattern, prev_prev_line, re.IGNORECASE) for pattern in COMMENT_PATTERNS):
                return "has_comment"
        
        return "no_comment"
        
    except Exception as e:
        return f"error: {str(e)}"

def process_assertion_file(csv_file_path):

    df = pd.read_csv(csv_file_path)
    

    df['assertion_category'] = ''
    df['has_comment'] = ''
    
    commented_count = 0
    

    for index, row in df.iterrows():

        category = classify_assertion(row['assertion_code'])
        df.at[index, 'assertion_category'] = category
        

        comment_status = check_assertion_comment(row['file_path'], row['line_number'], row['assertion_code'])
        df.at[index, 'has_comment'] = comment_status
        
        if comment_status == "has_comment":
            commented_count += 1
        

        if (index + 1) % 10 == 0:
            print(f"已处理 {index + 1}/{len(df)} 行")
    

    output_file = "assertion_analysis_result_2025.csv"
    df.to_csv(output_file, index=False)
    

    category_counts = df['assertion_category'].value_counts()
    print("\nAssertion分类统计:")
    for category, count in category_counts.items():
        print(f"{category}: {count}")
    
    return df

# 使用示例
if __name__ == "__main__":
    csv_file = "merged_assertion_property_2025.csv"、
    result_df = process_assertion_file(csv_file)
