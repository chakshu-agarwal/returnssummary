FROM public.ecr.aws/lambda/python:3.9

# Install the function's dependencies using pip
COPY requirements.txt .
RUN pip install --upgrade pip
COPY robin_stocks_no_pickle ./robin_stocks_no_pickle
RUN pip install -r requirements.txt

# Copy function code
COPY login_function.py .
COPY analysis_initiation.py .
COPY analysis_function.py .
COPY analysis_status.py .
COPY delete_report_function.py .
COPY analysislogout_function.py .
COPY resultslogout_function.py .
COPY robinhood_data_research_copy.py .

# # Set the CMD to your handler
# CMD ["index.lambda_handler"]