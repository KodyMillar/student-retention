# Student Retention App
This is a single-page application that receives, stores, and analyzes a school's student enrollment and drop out events in each semester. This app's main function is to perform an analysis on these events and is designed to be integrated with the school's main software that enrolls and removes students from the school's database. Users can view the results on the app's frontend. The purpose of this app is for school administrators, program heads, and deans to view the student retention rate, view the number of enrollments and drop outs in a given semester, and to compare the average gpa of enrolled students to the average gpa of student drop outs. This assists schools in ensuring they are maintaining a good student retention rate to ensure they are creating helpful and reasonable curriculums.

## Architecture
This app was created using a microservices architecture. Each service serves a specific functionality in the app. This is not to be confused with functions, as each service is comprised of multiple functions that make up a whole. Most of the services communicate asynchronously through a Kafka message broker, although one service communicates synchronously through REST API requests. Each service holds POST and/or GET REST API specifications through OpenAPI for the frontend to periodically request for updated data and analytics. The app uses periodic processing to retrieve and analyze newly received enrollment and drop out events. The app also uses a reverse proxy as an edge service to hide the service ip addresses and ports and only allow in HTTP traffic through a single base url. The app uses external configuration files to modify a service's settings and environment without needing to rebuild the service.

## Technologies
- **Nginx** as the proxy server
- **React** for the single-page frontend service
- **Python** for the backend services which receive, store, and analyze events and which check for event anomalies
- **Connexion** on top of Flask as the web framework to run the app and to use OpenAPI specification files
- **Python logger** for software tracing and event logging
- **MySQL** to store received events
- **JSON** to store and retrieve event analytics and anomalies
- **OpenAPI** and **Swagger** for API specifications for each service and to view each API in a UI format
- **Kafka** for asynchronous communication between services
- **Docker** to package each service in its own isolated Docker image
- **Docker Compose** to run all images at once and to scale each service to its desired amount
- **Jenkins** to run a CI/CD pipeline to build, test, package, and optionally deploy each service
- **AWS EC2** for a single-host deployment for all the services
- **Postman** to test out the API endpoints for each service
- **Jmeter** to test that the app properly updates itself after receiving many simultaneous requests
