from pydantic import BaseModel, Field, model_validator
from typing import List


class FileClassifaction(BaseModel):
    """
    Used to classify a file
    """

    file_id: int = Field(description="the original id of the file", example=[3, 30])
    file_name: str = Field(description="Name of the file", example="example.pdf")
    classification: str = Field(
        description="""Classification of the file which can be one of the following :
            - code_file
            - doc_file
            - configuration_file
            - other""",
        example="doc_file",
    )


def create_file_classification(
    file_name_for_verification: List[str], scores
) -> BaseModel:
    """
    input :
    file_name_for_verification  is used to check that all file are classified

    ouput :
        A type FileClassifications which all constrain used to classify files
    """

    class FileClassifications(BaseModel):
        """
        Model Used to classify files
        """

        file_classifications: List[FileClassifaction] = Field(
            description="List of file classifications",
            example=[
                {"file_name": "example.pdf", "classification": "doc_file"},
                {"file_name": "example.txt", "classification": "code_file"},
            ],
        )

        @model_validator(mode="after")
        def check_file_classification(cls, values):
            scores[0] += 1

            # Create sets of dictionaries for comparison
            classified_files = {
                (file_classification.file_name, file_classification.file_id)
                for file_classification in values.file_classifications
            }

            original_files = {
                (file_info["file_name"], file_info["file_id"])
                for file_info in file_name_for_verification
            }

            # Find missing and hallucinated files
            missing_files = original_files - classified_files
            hallucinated_files = classified_files - original_files

            # Prepare error message if needed
            error_messages = []

            if missing_files:
                missing_files_str = ", ".join(
                    f"(name: {name}, id: {id})" for name, id in missing_files
                )
                error_messages.append(
                    f"All files must be classified, you forgot these files: {missing_files_str}"
                )

            if hallucinated_files:
                hallucinated_files_str = ", ".join(
                    f"(name: {name}, id: {id})" for name, id in hallucinated_files
                )
                error_messages.append(
                    f"The original file names should be maintained, you hallucinated these files: {hallucinated_files_str}"
                )

            if error_messages:
                raise ValueError(" ".join(error_messages))

            return values

    return FileClassifications
