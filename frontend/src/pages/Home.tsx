import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import Loading from "../components/common/Loading";
import { getHealth } from "../services/healthService";

type ConnectionState = "checking" | "connected" | "offline";

export default function Home() {
  const [connectionState, setConnectionState] =
    useState<ConnectionState>("checking");

  useEffect(() => {
    let active = true;

    getHealth()
      .then(() => {
        if (active) {
          setConnectionState("connected");
        }
      })
      .catch(() => {
        if (active) {
          setConnectionState("offline");
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const statusLabel = {
    checking: "Checking...",
    connected: "Connected",
    offline: "Offline",
  }[connectionState];

  return (
    <main className="home-page">
      <section className="hero-panel">
        <div className="hero-copy">
          <p className="eyebrow">ADAPTIVE ANALYTICS WORKSPACE</p>
          <h1>Make every workflow<br /><em>fit the data.</em></h1>
          <p className="subtitle">From raw dataset to evidence-backed business priorities — with an adaptive workflow that makes each decision visible.</p>
          <div className="hero-actions">
            <Link className="primary-link" to="/upload">Start new analysis <span>→</span></Link>
            <a className="secondary-link" href="#workflow">Explore the workflow</a>
          </div>
        </div>
        <aside className="health-card">
          <span className={`status-dot ${connectionState}`} />
          <p>Platform status</p>
          {connectionState === "checking" ? <Loading message="Checking connection" /> : <strong>{statusLabel}</strong>}
          <small>{connectionState === "connected" ? "API and analytics services are ready" : "Start the backend to begin"}</small>
        </aside>
      </section>
      <section id="workflow" className="workflow-overview">
        <div className="section-intro"><p className="eyebrow">THE AWOF METHOD</p><h2>A transparent path from data to action.</h2><p>Each stage saves its result, explains why it ran, and prepares the next decision.</p></div>
        <div className="journey-grid">
          {[['01', 'Understand', 'Profile data quality, types, patterns, and risks.'], ['02', 'Adapt', 'Generate, prune, and execute the right workflow.'], ['03', 'Learn', 'Recommend, train, and evaluate suitable models.'], ['04', 'Prioritize', 'Explain outcomes and surface business priorities.']].map(([number, title, description]) => <article className="journey-card" key={number}><span>{number}</span><h3>{title}</h3><p>{description}</p></article>)}
        </div>
      </section>
    </main>
  );
}
