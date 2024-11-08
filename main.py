<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Upload Home</title>
    <link rel="stylesheet" href="/static/styles.css">
    <style>
        /* Modal styles */
        .modal {
            display: none;
            position: fixed;
            z-index: 1;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: rgb(0,0,0);
            background-color: rgba(0,0,0,0.4);
            padding-top: 60px;
        }
        .modal-content {
            background-color: #fefefe;
            margin: 5% auto;
            padding: 20px;
            border: 1px solid #888;
            width: 80%;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        .close {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
        }
        .close:hover,
        .close:focus {
            color: black;
            text-decoration: none;
            cursor: pointer;
        }
        .error { color: red; }
        .success { color: green; }
        .snackbar {
            visibility: hidden;
            min-width: 250px;
            background-color: #4CAF50; /* Success green background */
            color: #fff;
            text-align: left;
            border-radius: 8px;
            padding: 16px;
            position: fixed;
            z-index: 1;
            bottom: 20px;
            left: 20px;
            font-size: 16px;
            display: flex;
            align-items: center;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }

        .snackbar.show {
            visibility: visible;
            -webkit-animation: fadein 0.5s, fadeout 0.5s 3s;
            animation: fadein 0.5s, fadeout 0.5s 3s;
        }

        .snackbar-icon {
            margin-right: 10px;
            font-size: 20px;
        }

        @-webkit-keyframes fadein {
            from {bottom: 0; opacity: 0;}
            to {bottom: 20px; opacity: 1;}
        }

        @keyframes fadein {
            from {bottom: 0; opacity: 0;}
            to {bottom: 20px; opacity: 1;}
        }

        @-webkit-keyframes fadeout {
            from {bottom: 20px; opacity: 1;}
            to {bottom: 0; opacity: 0;}
        }

        @keyframes fadeout {
            from {bottom: 20px; opacity: 1;}
            to {bottom: 0; opacity: 0;}
        }

        .tab {
            display: inline-block;
            padding: 10px 20px;
            cursor: pointer;
            border: 1px solid #ccc;
            border-bottom: none;
            background-color: #f1f1f1;
        }

        .tab.active {
            background-color: #ffffff;
            border-bottom: 1px solid white;
            font-weight: bold;
        }

        .tab-content {
            border: 1px solid #ccc;
            padding: 20px;
            display: none;
        }

        .tab-content.active {
            display: block;
        }
        .pagination {
            margin-top: 20px;
            text-align: center;
        }
        .pagination a {
            margin: 0 5px;
            padding: 8px 16px;
            text-decoration: none;
            background-color: #f1f1f1;
            border: 1px solid #ccc;
            color: #333;
        }
        .pagination a.active {
            font-weight: bold;
            background-color: #4CAF50;
            color: white;
        }

    </style>
</head>
<body>
    <div class="container">
        <h1>File Uploads</h1>
        <div class="tabs">
            <div id="upload-tab" class="tab active" onclick="openTab('upload')">Upload</div>
            <div id="history-tab" class="tab" onclick="openTab('history')">Previous History</div>
            <div id="upload-config-tab" class="tab" onclick="openTab('upload-config')">Update Configurations</div>
        </div>
        <div id="upload-content" class="tab-content active">
        <div class="upload-container">
            <h2>Upload New File</h2>
            {% if error %}
                <p class="error">{{ error }}</p>
            {% elif message %}
                <p class="success">{{ message }}</p>
            {% endif %}
            <form action="/upload/" method="post" enctype="multipart/form-data" class="upload-form">
                <input type="file" name="file" required>
                <button type="submit" class="upload-button">Upload</button>
            </form>
        </div>

            </div>
        <div id="history-content" class="tab-content">
        <h2>Previous Uploads</h2>
        <table>
            <thead>
                <tr>
                    <th>CRM ID</th>
                    <th>Upload Owner</th>
                    <th>Upload Date</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {% for upload in uploads %}
                <tr>
                    <td><a href="#" class="crm-link" data-crm-id="{{ upload.crm_id }}">{{ upload.crm_id }}</a></td>
                    <td>{{ upload.owner }}</td>
                    <td>{{ upload.upload_date.strftime('%Y-%m-%d %H:%M:%S') }}</td>
                    <td>{{ upload.status }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
            <div class="pagination">
                {% for p in range(1, total_pages + 1) %}
    <a href="/?page={{ p }}" class="{{ 'active' if p == page else '' }}">{{ p }}</a>
{% endfor %}

{% if page < total_pages %}
    <a href="/?page={{ page + 1 }}">Next &raquo;</a>
{% endif %}
            </div>
            </div>

        <div id="upload-config-content" class="tab-content">
        <div class="upload-container">
            <h2>Upload Configurations File</h2>
            {% if error %}
                <p class="error">{{ error }}</p>
            {% elif message %}
                <p class="success">{{ message }}</p>
            {% endif %}
            <form action="/upload-configs/" method="post" enctype="multipart/form-data" class="upload-form">
                <input type="file" name="file" required>
                <button type="submit" class="upload-button">Upload</button>
            </form>
        </div>

            </div>


            </div>


    <!-- Modal -->
    <div id="myModal" class="modal">
        <div class="modal-content">
            <span class="close">&times;</span>
            <h2>Upload History</h2>
            <table id="history-table">
                <thead>
                    <tr>
                        <th>Upload Date</th>
                        <th>Status</th>
                        <th>Owner</th>
                        <th>Error Message</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- History records will be inserted here -->
                </tbody>
            </table>

        </div>
    </div>

    {% if message %}
    <div id="snackbar" class="snackbar">
        <span class="snackbar-icon">✔️</span> <!-- Success icon -->
        <span id="snackbar-message">{{ message }}</span>
    </div>
    {% endif %}



    <script>
        const modal = document.getElementById("myModal");
        const span = document.getElementsByClassName("close")[0];

        document.querySelectorAll('.crm-link').forEach(link => {
            link.onclick = async function(event) {
                event.preventDefault();
                const crmId = this.getAttribute("data-crm-id");
                const response = await fetch(`/upload_history/${crmId}`);
                const history = await response.json();

                const tbody = document.getElementById("history-table").getElementsByTagName("tbody")[0];
                tbody.innerHTML = ""; // Clear previous data

                history.forEach(upload => {
                    const row = tbody.insertRow();
                    row.insertCell(0).innerText = new Date(upload.upload_date).toLocaleDateString();
                    row.insertCell(1).innerText = upload.status;
                    row.insertCell(2).innerText = upload.owner;
                    row.insertCell(3).innerText = upload.error ? upload.error : "None";
                });

                modal.style.display = "block";
            };
        });

        span.onclick = function() {
            modal.style.display = "none";
        };

        window.onclick = function(event) {
            if (event.target === modal) {
                modal.style.display = "none";
            }
        };


        window.onload = function() {
            const message = "{{message}}"
            const snackbar = document.getElementById("snackbar");
            console.log("This is message", message)
            if (message !== "") {
                snackbar.classList.add("show");
                setTimeout(() => snackbar.classList.remove("show"), 3000);
            }
        }
        function openTab(tabName) {
            // Remove active class from all tabs and contents
            document.querySelectorAll('.tab, .tab-content').forEach(element => {
                element.classList.remove('active');
            });

            // Add active class to selected tab and content
            document.getElementById(tabName + '-tab').classList.add('active');
            document.getElementById(tabName + '-content').classList.add('active');
        }
        const urlParams = new URLSearchParams(window.location.search);
            const page = urlParams.get('page'); // Get the `page` query parameter

            if (page) {
                // If there's a page parameter in the URL, activate the 'history' tab
                openTab('history');
            } else {
                // If there's no page parameter, activate the 'upload' tab by default
                openTab('upload');
            }
    </script>
</body>
</html>
