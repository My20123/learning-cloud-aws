document
  .getElementById("upload-form")
  .addEventListener("submit", async function (event) {
    event.preventDefault()

    const fileInput = document.getElementById("file")
    const file = fileInput.files[0]

    if (!file) {
      alert("Please choose a file to upload.")
      return
    }

    const formData = new FormData()
    formData.append("file", file)

    try {
      const response = await fetch("/upload", {
        method: "POST",
        body: formData,
      })

      if (response.ok) {
        alert("File uploaded successfully.")
        fetchFileList() // Refresh the file list after upload
      } else {
        alert("Failed to upload the file.")
      }
    } catch (error) {
      console.error("Error:", error)
      alert("Error uploading the file.")
    }
  })
