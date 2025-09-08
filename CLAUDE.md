# Sumo News Digest - Claude Commands

## Commands to run to test the system:
- `npm run lint` - Run linting (not applicable, Python project)
- `npm run typecheck` - Run type checking (not applicable, Python project)
- `python main.py --dry-run` - Test complete pipeline without sending emails
- `python tests/test_pipeline.py` - Test pipeline and generate output files
- `python main.py --test` - Test all components

## Project Context:
- This is an AI-powered sumo news digest emailer
- Uses vector database (sqlite-vec) for semantic similarity
- Includes educational "Bite-sized Sumo" content in emails  
- Prevents duplicate content across email sends
- Remember project scope and intent