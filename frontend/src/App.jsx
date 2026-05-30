import { useState } from "react";
import axios from "axios";

function App() {

  const [topic,setTopic] = useState("");
  const [report,setReport] = useState("");

  const generateReport = async () => {

    const res = await axios.post(
      "http://localhost:8000/research",
      {
        topic
      }
    );

    setReport(res.data.report);
  };

  return (
    <div>

      <h1>AI Research Assistant</h1>

      <input
        value={topic}
        onChange={(e)=>setTopic(e.target.value)}
        placeholder="Research Topic"
      />

      <button
        onClick={generateReport}
      >
        Research
      </button>

      <pre>{report}</pre>

    </div>
  );
}

export default App;