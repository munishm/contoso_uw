"""Azure Content Understanding Client."""

import logging
import time
import requests
from typing import Dict, Any, Optional, Callable
from pathlib import Path


class AzureContentUnderstandingClient:
    """
    Azure Content Understanding Client.
    
    Based on official Azure samples:
    https://github.com/Azure-Samples/azure-ai-content-understanding-python
    """
    
    def __init__(
        self,
        endpoint: str,
        api_version: str,
        subscription_key: Optional[str] = None,
        token_provider: Optional[Callable] = None,
        x_ms_useragent: str = "hsbc-document-classification"
    ):
        """
        Initialize the Azure Content Understanding client.
        
        Args:
            endpoint: Azure Content Understanding endpoint URL
            api_version: API version to use
            subscription_key: Optional subscription key for authentication
            token_provider: Optional callable that returns access token
            x_ms_useragent: User agent string for requests
        """
        if not subscription_key and not token_provider:
            raise ValueError("Either subscription key or token provider must be provided.")
        if not api_version:
            raise ValueError("API version must be provided.")
        if not endpoint:
            raise ValueError("Endpoint must be provided.")

        self._endpoint = endpoint.rstrip("/")
        self._api_version = api_version
        self._logger = logging.getLogger(__name__)

        token = token_provider() if token_provider else None
        self._headers = self._get_headers(subscription_key, token, x_ms_useragent)

    def _get_headers(
        self, 
        subscription_key: Optional[str], 
        api_token: Optional[str], 
        x_ms_useragent: str
    ) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {"User-Agent": x_ms_useragent}
        if subscription_key:
            headers["Ocp-Apim-Subscription-Key"] = subscription_key
        elif api_token:
            headers["Authorization"] = f"Bearer {api_token}"
        return headers

    def _raise_for_status_with_detail(self, response: requests.Response):
        """Raise detailed error for failed requests."""
        if not response.ok:
            error_message = f"HTTP {response.status_code}"
            try:
                error_detail = response.json()
                self._logger.error(f"HTTP {response.status_code}: {error_detail}")
                # Extract more specific error message if available
                if isinstance(error_detail, dict):
                    error_message = error_detail.get('error', {}).get('message', str(error_detail))
            except:
                error_message = response.text
                self._logger.error(f"HTTP {response.status_code}: {response.text}")
            
            # Raise with detailed message
            raise requests.exceptions.HTTPError(
                f"{response.status_code} Error: {error_message} for url: {response.url}",
                response=response
            )

    def check_analyzer_exists(self, analyzer_id: str) -> bool:
        """
        Check if an analyzer/classifier exists.
        
        Args:
            analyzer_id: ID of the analyzer to check
            
        Returns:
            True if analyzer exists, False otherwise
        """
        try:
            url = f"{self._endpoint}/contentunderstanding/analyzers/{analyzer_id}?api-version={self._api_version}"
            headers = {"Content-Type": "application/json"}
            headers.update(self._headers)
            
            response = requests.get(url, headers=headers)
            return response.status_code == 200
        except Exception as e:
            self._logger.debug(f"Error checking analyzer existence: {e}")
            return False

    def begin_create_classifier(
        self, 
        classifier_id: str, 
        classifier_schema: Dict[str, Any]
    ) -> requests.Response:
        """
        Create a Content Understanding classifier.
        
        Args:
            classifier_id: Unique identifier for the classifier
            classifier_schema: Classifier configuration schema
            
        Returns:
            Response from the creation request
        """
        if not classifier_schema:
            raise ValueError("Classifier schema must be provided.")
        if not classifier_id:
            raise ValueError("Classifier ID must be provided.")

        headers = {"Content-Type": "application/json"}
        headers.update(self._headers)

        url = f"{self._endpoint}/contentunderstanding/analyzers/{classifier_id}?api-version={self._api_version}"
        
        self._logger.info(f"Creating classifier at: {url}")
        self._logger.debug(f"Classifier schema: {classifier_schema}")
        
        response = requests.put(
            url=url,
            headers=headers,
            json=classifier_schema,
        )
        
        if not response.ok:
            self._logger.error(f"Classifier creation failed - Request body: {classifier_schema}")
            
        self._raise_for_status_with_detail(response)
        self._logger.info(f"Classifier {classifier_id} creation request accepted.")
        return response

    def classify_document(
        self, 
        classifier_id: str, 
        file_path: str
    ) -> requests.Response:
        """
        Classify a document using Azure Content Understanding.
        
        Args:
            classifier_id: The ID of the classifier to use
            file_path: Local path to the file to classify
            
        Returns:
            Response from the classification request
        """
        if not Path(file_path).exists():
            raise ValueError(f"File not found: {file_path}")
        
        with open(file_path, "rb") as file:
            file_data = file.read()
        
        headers = {"Content-Type": "application/octet-stream"}
        headers.update(self._headers)
        
        url = f"{self._endpoint}/contentunderstanding/analyzers/{classifier_id}:analyzeBinary?api-version={self._api_version}"
        
        response = requests.post(
            url=url,
            headers=headers,
            data=file_data,
        )
        
        self._raise_for_status_with_detail(response)
        self._logger.info(f"Classifying file {file_path} with classifier: {classifier_id}")
        return response

    def poll_result(
        self, 
        response: requests.Response, 
        timeout_seconds: int = 180, 
        polling_interval_seconds: int = 2
    ) -> Dict[str, Any]:
        """
        Poll for operation completion and return results.
        
        Args:
            response: Response from classification or creation request
            timeout_seconds: Maximum time to wait for completion
            polling_interval_seconds: Time between polling attempts
            
        Returns:
            Final result from the operation
        """
        operation_location = response.headers.get("Operation-Location")
        if not operation_location:
            raise ValueError("No Operation-Location header found in response")

        headers = {"Content-Type": "application/json"}
        headers.update(self._headers)

        start_time = time.time()
        while True:
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout_seconds:
                raise TimeoutError(f"Operation timed out after {timeout_seconds:.2f} seconds.")

            poll_response = requests.get(operation_location, headers=headers)
            self._raise_for_status_with_detail(poll_response)
            
            result = poll_response.json()
            status = result.get("status", "").lower()
            
            if status == "succeeded":
                self._logger.info(f"Request completed after {elapsed_time:.2f} seconds.")
                return result
            elif status == "failed":
                error_msg = result.get("error", {}).get("message", "Unknown error")
                self._logger.error(f"Request failed: {error_msg}")
                raise RuntimeError(f"Operation failed: {error_msg}")
            else:
                self._logger.debug(f"Status: {status}, polling...")
                time.sleep(polling_interval_seconds)

    def delete_analyzer(self, analyzer_id: str) -> requests.Response:
        """Delete an analyzer/classifier."""
        url = f"{self._endpoint}/contentunderstanding/analyzers/{analyzer_id}?api-version={self._api_version}"
        response = requests.delete(url, headers=self._headers)
        self._raise_for_status_with_detail(response)
        return response
