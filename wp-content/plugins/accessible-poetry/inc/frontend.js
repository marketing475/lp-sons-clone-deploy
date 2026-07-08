// Function for sending data
function sendDataAccessibleWP() {
    // Creating an object to send
    const eventData = {
      events: [ {
        "event": "Accessibility-Toolbar-click",
        "content": "user click Accessibility Toolbar button",
        "siteUrl": AccessibleWPData.siteUrl,
    } ]
      
    };
  
    // Converting Data to JSON String
    const jsonData = JSON.stringify(eventData);
  
    // Sending a request using the Fetch API
    fetch('https://api.userway.org/api/abn/events', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonData,
    })
      .then(response => {
        if (!response.ok) {
          throw new Error('An error occurred while executing the request: ${response.statusText}');
        }
        return response.json();
      })
      .then(data => {
        // Handling a successful response from the server
        console.log('Response from the server:', data);
      })
      .catch(error => {
        // Error processing
        console.error('An error has occurred:', error.message);
      });
}
  
// Attach the function to the button's click event
document.addEventListener('DOMContentLoaded', (event) => {
    const wpButton = document.getElementById('acwp-toolbar-btn');
    if (wpButton) {
      wpButton.addEventListener('click', sendDataAccessibleWP);
    } else {
        console.error('Button with ID "plugin-button-notice" not found.');
    }
});










  // Function for sending data page first time load
function sendDataPageLoad() {
  // Creating an object to send
  const eventData = {
    events: [{
      "event": "Accessibility-Page-load",
      "content": "Page load with AccessibleWP widget",
      "siteUrl": AccessibleWPData.siteUrl,
    }]
  };

  // Converting Data to JSON String
  const jsonData = JSON.stringify(eventData);

  // Sending a request using the Fetch API
  fetch('https://api.userway.org/api/abn/events', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: jsonData,
  })
  .then(response => {
    if (!response.ok) {
      throw new Error(`An error occurred while executing the request: ${response.statusText}`);
    }
    return response.json();
  })
  .then(data => {
    // Handling a successful response from the server
    console.log('Response from the server:', data);
  })
  .catch(error => {
    // Error processing
    console.error('An error has occurred:', error.message);
  });
}

// Function to check if it's the first page load in the session
function checkFirstLoadAndSendData() {
  // Check if the data has already been sent in this session
  if (!sessionStorage.getItem('dataSent')) {
    // If not, send the data and set the flag
    sendDataPageLoad();
    sessionStorage.setItem('dataSent', 'true');
  }
}

// Attach the function to the document's load event
document.addEventListener('DOMContentLoaded', (event) => {
  // Send data on first page load in the session
  checkFirstLoadAndSendData();
});
  