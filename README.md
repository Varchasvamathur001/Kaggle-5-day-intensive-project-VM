# Kaggle-5-day-intensive-project-VM
This is my Capstone Project for the Kaggle 5-Day AI Agents: Intensive Vibe Coding Course With Google. It is to show how I created an AI accounting Agent.

# Business Accounting Agent: Automated Invoice Processor
I built this project to solve a problem I've seen in a lot of small business workflows: manually sorting through stacks of invoices and trying to figure out which ones need urgent attention. 
Instead of doing that by hand, I created an Agent that scans a folder of invoices, pulls out the key data (vendor, date, and total amount), and generates a neat summary report for you. It even automatically flags any invoice over $500 as "High Priority" so you know exactly where to focus.

## How it Works
The project uses a simple agentic workflow:
* **The Brain (`system_prompt.md`):** Sets the rules and tone for how the agent handles financial data.
* **The Hands (`tools.py`):** Uses Python and Regex to "read" the text files and extract the info we need.
* **The Logic:** It processes a whole folder (`Sample-data/`) at once, saving the result into a clean `summary_report.json`.

## How to Run This
You'll need Python installed on your machine. 
1. Clone this repository to your computer.
2. Put your invoice text files into the `Sample-data/` folder.
3. Run the following command in your terminal:

```bash
python -c "import tools; print(tools.process_all_invoices('Sample-data'))"
