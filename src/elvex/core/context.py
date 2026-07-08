# Objective: Store and pass information between agents without putting everything into the prompt.
# Shared system memory
#
# Example:
#   • Worker A generates a long analysis.
#   • Worker B only needs:
#       • a summary
#       • 3 key points
#
# This is decided and managed by context.py.
#
# This helps avoid:
#   • huge prompts
#   • loss of information
#   • the famous "dumb zone"