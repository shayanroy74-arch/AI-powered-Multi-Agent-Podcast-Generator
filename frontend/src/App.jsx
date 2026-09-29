import { useState } from "react";
import "./App.css";

const API_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function App() {
  const [title, setTitle] = useState("");
  const [topic, setTopic] = useState("");
  const [duration, setDuration] = useState(20);
  const [language, setLanguage] = useState("English");
  const [speakers, setSpeakers] = useState(2);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [generationStep, setGenerationStep] = useState("");
  const [podcastResult, setPodcastResult] = useState(null);

  const [view, setView] = useState("home");
  const [podcasts, setPodcasts] = useState([]);
  const [loadingPodcasts, setLoadingPodcasts] = useState(false);
  const [selectedPodcast, setSelectedPodcast] = useState(null);
const [loadingPodcastDetails, setLoadingPodcastDetails] = useState(false);

  // =========================================================
  // CREATE + GENERATE PODCAST
  // =========================================================

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setSuccess("");
    setGenerationStep("");
    setPodcastResult(null);
    setLoading(true);

    try {
      // ==========================================
      // STEP 1: CREATE PODCAST
      // ==========================================

      const createResponse = await fetch(
        `${API_URL}/podcasts`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            user_id: 1,
            title: title,
            topic: topic,
            duration: duration,
            language: language,
            speakers: speakers,
            status: "draft",
          }),
        }
      );

      if (!createResponse.ok) {
        throw new Error("Failed to create podcast");
      }

      const podcastData = await createResponse.json();
      const podcastId = podcastData.podcast_id;

      console.log("Podcast created:", podcastData);

      // ==========================================
      // STEP 2: START GENERATION
      // ==========================================

      const generationResponse = await fetch(
        `${API_URL}/generate-podcast`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            podcast_id: podcastId,
          }),
        }
      );

      if (!generationResponse.ok) {
        throw new Error("Failed to start podcast generation");
      }

      const generationData = await generationResponse.json();

      console.log("Generation started:", generationData);

      setGenerationStep(
        generationData.current_step || "researching"
      );

      // ==========================================
      // STEP 3: MONITOR GENERATION
      // ==========================================

      let completed = false;

      while (!completed) {
        await new Promise((resolve) =>
          setTimeout(resolve, 2000)
        );

        const statusResponse = await fetch(
          `${API_URL}/podcasts/${podcastId}/status`,
          {
            cache: "no-store",
          }
        );

        if (!statusResponse.ok) {
          continue;
        }

        const statusData = await statusResponse.json();

        console.log(
          "Generation status:",
          statusData
        );

        setGenerationStep(
          statusData.current_step ||
            statusData.status
        );

        // ========================================
        // GENERATION FAILED
        // ========================================

        if (statusData.status === "failed") {
          completed = true;

          throw new Error(
            "Podcast generation failed."
          );
        }

        // ========================================
        // GENERATION COMPLETED
        // ========================================

        if (statusData.status === "completed") {
          completed = true;

          setGenerationStep("completed");

          console.log(
            "Podcast generation completed."
          );

          // ======================================
          // STEP 4: GET COMPLETED PODCAST DETAILS
          // ======================================

          const detailsResponse = await fetch(
            `${API_URL}/podcasts/${podcastId}`
          );

          if (!detailsResponse.ok) {
            throw new Error(
              "Failed to load generated podcast"
            );
          }

          const detailsData =
            await detailsResponse.json();

          console.log(
            "Podcast details:",
            detailsData
          );

          setPodcastResult(detailsData);

          setSuccess(
            `Podcast #${podcastId} generated successfully!`
          );
        }
      }
    } catch (error) {
      console.error(
        "Podcast generation failed:",
        error
      );

      setError(
        error.message ||
          "Something went wrong."
      );
    } finally {
      setLoading(false);
    }
  };

  // =========================================================
  // LOAD MY PODCASTS
  // =========================================================

  const loadPodcasts = async () => {
    setLoadingPodcasts(true);
    setError("");
    setSuccess("");

    try {
      const response = await fetch(
        `${API_URL}/podcasts`
      );

      if (!response.ok) {
        throw new Error(
          "Failed to load podcasts"
        );
      }

      const data = await response.json();

      setPodcasts(data);
      setView("podcasts");
    } catch (error) {
      console.error(
        "Failed to load podcasts:",
        error
      );

      setError(
        error.message ||
          "Failed to load podcasts."
      );
    } finally {
      setLoadingPodcasts(false);
    }
  };

  const openPodcast = async (podcastId) => {
  setLoadingPodcastDetails(true);
  setError("");

  try {
    const response = await fetch(
      `${API_URL}/podcasts/${podcastId}`
    );

    if (!response.ok) {
      throw new Error(
        "Failed to load podcast details"
      );
    }

    const data = await response.json();

    console.log(
      "Podcast details:",
      data
    );

    setSelectedPodcast(data);
    setView("details");

  } catch (error) {
    console.error(
      "Failed to load podcast details:",
      error
    );

    setError(
      error.message ||
        "Failed to load podcast details."
    );

  } finally {
    setLoadingPodcastDetails(false);
  }
};

const regeneratePodcast = async () => {
  if (!selectedPodcast) {
    return;
  }

  const podcastId = selectedPodcast.podcast.id;

  setError("");
  setSuccess("");
  setLoading(true);
  setGenerationStep("researching");

  try {
    const response = await fetch(
      `${API_URL}/podcasts/${podcastId}/regenerate`,
      {
        method: "POST",
      }
    );

    if (!response.ok) {
      throw new Error(
        "Failed to regenerate podcast"
      );
    }

    const data = await response.json();

    console.log(
      "Regeneration started:",
      data
    );

    // Monitor regeneration
    let completed = false;

    while (!completed) {
      await new Promise((resolve) =>
        setTimeout(resolve, 2000)
      );

      const statusResponse = await fetch(
        `${API_URL}/podcasts/${podcastId}/status`
      );

      if (!statusResponse.ok) {
        continue;
      }

      const statusData =
        await statusResponse.json();

      console.log(
        "Regeneration status:",
        statusData
      );

      setGenerationStep(
        statusData.current_step ||
          statusData.status
      );

      if (statusData.status === "failed") {
        completed = true;

        throw new Error(
          "Podcast regeneration failed."
        );
      }

      if (statusData.status === "completed") {
        completed = true;

        setGenerationStep("completed");

        // Get the newly generated podcast
        const detailsResponse =
          await fetch(
            `${API_URL}/podcasts/${podcastId}`
          );

        if (!detailsResponse.ok) {
          throw new Error(
            "Failed to load regenerated podcast"
          );
        }

        const detailsData =
          await detailsResponse.json();

        setSelectedPodcast(detailsData);
        setPodcastResult(detailsData);

        setSuccess(
          "Podcast regenerated successfully!"
        );
      }
    }

  } catch (error) {
    console.error(
      "Podcast regeneration failed:",
      error
    );

    setError(
      error.message ||
        "Failed to regenerate podcast."
    );

  } finally {
    setLoading(false);
  }
};

const deletePodcast = async () => {
  if (!selectedPodcast) {
    return;
  }

  const podcastId =
    selectedPodcast.podcast.id;

  const confirmed = window.confirm(
    "Are you sure you want to delete this podcast?"
  );

  if (!confirmed) {
    return;
  }

  setError("");

  try {
    const response = await fetch(
      `${API_URL}/podcasts/${podcastId}`,
      {
        method: "DELETE",
      }
    );

    if (!response.ok) {
      throw new Error(
        "Failed to delete podcast"
      );
    }

    console.log(
      "Podcast deleted:",
      podcastId
    );

    setSelectedPodcast(null);

    // Refresh podcast library
    await loadPodcasts();

  } catch (error) {
    console.error(
      "Failed to delete podcast:",
      error
    );

    setError(
      error.message ||
        "Failed to delete podcast."
    );
  }
};
  // =========================================================
  // RETURN
  // =========================================================

  return (
    <div className="app">

      {/* =====================================================
          NAVBAR
      ===================================================== */}

      <nav className="navbar">

        <div className="logo">
          Podcaster
        </div>

        <div className="nav-links">

          <span
            onClick={() => {
              setView("home");
              setError("");
            }}
          >
            Dashboard
          </span>

          <span
            onClick={loadPodcasts}
          >
            My Podcasts
          </span>

        </div>

      </nav>


      {/* =====================================================
          MAIN CONTENT
      ===================================================== */}

      <main className="main-content">

        {/* ===================================================
            MY PODCASTS PAGE
        =================================================== */}

        {view === "podcasts" && (
          <section className="podcasts-page">

            <div className="podcasts-header">

              <div>

                <p className="eyebrow">
                  YOUR LIBRARY
                </p>

                <h1>
                  My Podcasts
                </h1>

                <p>
                  Your generated and saved
                  podcasts.
                </p>

              </div>

              <button
                className="new-podcast-button"
                onClick={() => {
                  setView("home");
                  setError("");
                }}
              >
                + New Podcast
              </button>

            </div>


            {/* Loading */}

            {loadingPodcasts && (
              <div className="loading-message">
                Loading podcasts...
              </div>
            )}


            {/* Empty state */}

            {!loadingPodcasts &&
              podcasts.length === 0 && (
                <div className="empty-state">

                  <h2>
                    No podcasts yet
                  </h2>

                  <p>
                    Create your first
                    AI-powered podcast.
                  </p>

                  <button
                    className="generate-button"
                    onClick={() =>
                      setView("home")
                    }
                  >
                    Create Podcast
                  </button>

                </div>
              )}


            {/* Podcast cards */}

            {!loadingPodcasts &&
              podcasts.length > 0 && (
                <div className="podcast-grid">

                  {podcasts.map(
                    (podcast) => (
                      <div
  className="podcast-card"
  key={podcast.id}
  onClick={() => openPodcast(podcast.id)}
>

                        <div className="podcast-card-top">

                          <h2>
                            {podcast.title}
                          </h2>

                          <span
                            className={`status-badge ${
                              podcast.status ||
                              "draft"
                            }`}
                          >
                            {podcast.status === "completed"
                              ? "Completed"
                              : podcast.status === "generating"
                              ? "Generating"
                              : podcast.status === "failed"
                              ? "Failed"
                              : "Draft"}
                          </span>

                        </div>

                        <p className="podcast-topic">
                          {podcast.topic}
                        </p>

                        {podcast.status === "generating" &&
                          podcast.current_step && (
                            <p className="podcast-progress">
                              {podcast.current_step === "researching" &&
                                "Researching topic..."}

                              {podcast.current_step === "outlining" &&
                                "Creating outline..."}

                              {podcast.current_step === "writing_host" &&
                                "Writing host dialogue..."}

                              {podcast.current_step === "writing_guest" &&
                                "Writing guest dialogue..."}

                              {podcast.current_step === "reviewing" &&
                                "Reviewing script..."}

                              {podcast.current_step === "generating_audio" &&
                                "Generating audio..."}

                              {podcast.current_step === "failed" &&
                                "Generation failed."}
                            </p>
                          )}

                        <div className="podcast-meta">

                          <span>
                            {podcast.duration ||
                              "--"}{" "}
                            min
                          </span>

                          <span>
                            {podcast.language ||
                              "English"}
                          </span>

                          <span>
                            {podcast.speakers ||
                              2}{" "}
                            speakers
                          </span>

                        </div>

                      </div>
                    )
                  )}

                </div>
              )}

          </section>
        )}

        {view === "details" && (
  <section className="podcast-details-page">

    {loadingPodcastDetails && (
      <div className="loading-message">
        Loading podcast...
      </div>
    )}

    {!loadingPodcastDetails &&
      selectedPodcast && (
        <>

          {/* Back button */}

          <button
            className="back-button"
            onClick={() => {
              setSelectedPodcast(null);
              setView("podcasts");
            }}
          >
            ← Back to My Podcasts
          </button>


          {/* Header */}

          <div className="details-header">

  <div className="details-header-content">

    <div>

      <p className="eyebrow">
        PODCAST
      </p>

      <h1>
        {selectedPodcast.podcast.title}
      </h1>

      <p>
        {selectedPodcast.podcast.topic}
      </p>

    </div>

    <div className="details-actions">

  <button
    className="regenerate-button"
    onClick={regeneratePodcast}
    disabled={loading}
  >
    {loading
      ? "Regenerating..."
      : "↻ Regenerate Podcast"}
  </button>

  <button
    className="delete-button"
    onClick={deletePodcast}
    disabled={loading}
  >
    Delete
  </button>

</div>

  </div>

</div>

{loading && (
  <div className="generation-status">

    <div className="status-spinner"></div>

    <div>

      <strong>
        Regenerating your podcast
      </strong>

      <p>

        {generationStep ===
          "researching" &&
          "Researching the topic..."}

        {generationStep ===
          "outlining" &&
          "Creating the podcast outline..."}

        {generationStep ===
          "writing_host" &&
          "Writing the host dialogue..."}

        {generationStep ===
          "writing_guest" &&
          "Writing the guest dialogue..."}

        {generationStep ===
          "reviewing" &&
          "Reviewing and assembling the final script..."}

        {generationStep ===
          "generating_audio" &&
          "Generating podcast audio..."}

        {!generationStep &&
          "Starting regeneration..."}

      </p>

    </div>

  </div>
)}


          {/* Audio */}

          {selectedPodcast.audio && (
            <div className="details-card audio-card">

              <h2>
                Your Podcast
              </h2>

              <audio
                controls
                src={`${API_URL}${selectedPodcast.audio.url}`}
              />

            </div>
          )}


          {/* Script */}

          {selectedPodcast.script && (
            <div className="details-card content-card">

              <h2>
                Podcast Script
              </h2>

              <pre>
                {selectedPodcast.script.content}
              </pre>

            </div>
          )}


          {/* Research */}

          {selectedPodcast.research && (
            <div className="details-card content-card">

              <h2>
                Research
              </h2>

              <pre>
                {selectedPodcast.research.content}
              </pre>

            </div>
          )}


          {/* Outline */}

          {selectedPodcast.outline && (
            <div className="details-card content-card">

              <h2>
                Podcast Outline
              </h2>

              <pre>
                {selectedPodcast.outline.content}
              </pre>

            </div>
          )}

        </>
      )}

  </section>
)}
        {/* ===================================================
            HOME / CREATE PODCAST PAGE
        =================================================== */}

        {view === "home" && (
          <>

            {/* =================================================
                HERO + CREATE PODCAST
            ================================================= */}

            <section className="hero-section">

              {/* Hero */}

              <div className="hero-text">

                <p className="eyebrow">
                  AI-POWERED PODCAST GENERATOR
                </p>

                <h1>
                  Turn an idea into a
                  <span> podcast.</span>
                </h1>

                <p className="hero-description">
                  Create research, scripts,
                  conversations and realistic
                  podcast audio using a team of
                  AI agents.
                </p>

              </div>


              {/* Create Podcast Card */}

              <div className="create-card">

                <h2>
                  Create a Podcast
                </h2>

                <p className="card-description">
                  Tell us what you want your
                  podcast to be about.
                </p>


                <form
                  onSubmit={handleSubmit}
                >

                  {/* Title */}

                  <div className="form-group">

                    <label htmlFor="title">
                      Podcast Title
                    </label>

                    <input
                      id="title"
                      type="text"
                      placeholder="e.g. The Future of AI"
                      value={title}
                      onChange={(event) =>
                        setTitle(
                          event.target.value
                        )
                      }
                      required
                      disabled={loading}
                    />

                  </div>


                  {/* Topic */}

                  <div className="form-group">

                    <label htmlFor="topic">
                      Topic
                    </label>

                    <textarea
                      id="topic"
                      placeholder="What should the podcast discuss?"
                      value={topic}
                      onChange={(event) =>
                        setTopic(
                          event.target.value
                        )
                      }
                      rows="4"
                      required
                      disabled={loading}
                    />

                  </div>


                  {/* Duration + Language */}

                  <div className="form-row">

                    <div className="form-group">

                      <label htmlFor="duration">
                        Duration
                      </label>

                      <select
                        id="duration"
                        value={duration}
                        onChange={(event) =>
                          setDuration(
                            Number(
                              event.target.value
                            )
                          )
                        }
                        disabled={loading}
                      >

                        <option value={10}>
                          10 minutes
                        </option>

                        <option value={15}>
                          15 minutes
                        </option>

                        <option value={20}>
                          20 minutes
                        </option>

                        <option value={30}>
                          30 minutes
                        </option>

                        <option value={45}>
                          45 minutes
                        </option>

                        <option value={60}>
                          60 minutes
                        </option>

                      </select>

                    </div>


                    <div className="form-group">

                      <label htmlFor="language">
                        Language
                      </label>

                      <select
                        id="language"
                        value={language}
                        onChange={(event) =>
                          setLanguage(
                            event.target.value
                          )
                        }
                        disabled={loading}
                      >

                        <option value="English">
                          English
                        </option>

                        <option value="Hindi">
                          Hindi
                        </option>

                        <option value="Bengali">
                          Bengali
                        </option>

                      </select>

                    </div>

                  </div>


                  {/* Speakers */}

                  <div className="form-group">

                    <label htmlFor="speakers">
                      Number of Speakers
                    </label>

                    <select
                      id="speakers"
                      value={speakers}
                      onChange={(event) =>
                        setSpeakers(
                          Number(
                            event.target.value
                          )
                        )
                      }
                      disabled={loading}
                    >

                      <option value={2}>
                        2 speakers
                      </option>

                      <option value={3}>
                        3 speakers
                      </option>

                      <option value={4}>
                        4 speakers
                      </option>

                    </select>

                  </div>


                  {/* Error */}

                  {error && (
                    <div className="error-message">
                      {error}
                    </div>
                  )}


                  {/* Success */}

                  {success && (
                    <div className="success-message">
                      {success}
                    </div>
                  )}


                  {/* Generation Status */}

                  {loading && (
                    <div className="generation-status">

                      <div className="status-spinner"></div>

                      <div>

                        <strong>
                          Generating your podcast
                        </strong>

                        <p>

                          {generationStep ===
                            "researching" &&
                            "Researching the topic..."}

                          {generationStep ===
                            "outlining" &&
                            "Creating the podcast outline..."}

                          {generationStep ===
                            "writing_host" &&
                            "Writing the host dialogue..."}

                          {generationStep ===
                            "writing_guest" &&
                            "Writing the guest dialogue..."}

                          {generationStep ===
                            "reviewing" &&
                            "Reviewing and assembling the final script..."}

                          {generationStep ===
                            "generating_audio" &&
                            "Generating podcast audio..."}

                          {!generationStep &&
                            "Starting generation..."}

                        </p>

                      </div>

                    </div>
                  )}


                  {/* Generate Button */}

                  <button
                    type="submit"
                    className="generate-button"
                    disabled={loading}
                  >

                    {loading
                      ? "Generating Podcast..."
                      : "Generate Podcast"}

                  </button>

                </form>

              </div>

            </section>


            {/* =================================================
                SUCCESS RESULT
            ================================================= */}

            {podcastResult && (
              <section className="podcast-result">

                <div className="result-header">

                  <div>

                    <p className="eyebrow">
                      PODCAST GENERATED
                    </p>

                    <h2>
                      {
                        podcastResult.podcast
                          .title
                      }
                    </h2>

                    <p>
                      {
                        podcastResult.podcast
                          .topic
                      }
                    </p>

                  </div>

                  <span className="completed-badge">
                    Completed
                  </span>

                </div>


                {/* Audio */}

                {podcastResult.audio && (
                  <div className="audio-card">

                    <h3>
                      Your Podcast
                    </h3>

                    <audio
                      controls
                      src={`${API_URL}${podcastResult.audio.url}`}
                    />

                  </div>
                )}


                {/* Script */}

                {podcastResult.script && (
                  <div className="content-card">

                    <h3>
                      Podcast Script
                    </h3>

                    <pre>
                      {
                        podcastResult.script
                          .content
                      }
                    </pre>

                  </div>
                )}

              </section>
            )}

          </>
        )}

      </main>

    </div>
  );
}

export default App;