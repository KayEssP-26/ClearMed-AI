import { motion } from "motion/react";

export function LandingHero() {
  return (
    <section className="landing-hero" aria-labelledby="landing-title">
      <motion.div
        className="hero-orbit hero-orbit-one"
        aria-hidden="true"
        animate={{ y: [0, -12, 0], rotate: [0, 4, 0] }}
        transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="hero-orbit hero-orbit-two"
        aria-hidden="true"
        animate={{ y: [0, 10, 0], rotate: [0, -5, 0] }}
        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="landing-content"
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.55, ease: "easeOut" }}
      >
        <p className="eyebrow">Medical language, made more human</p>
        <h1 id="landing-title">A clearer way to read your health information.</h1>
        <p className="landing-intro">
          ClearMed AI turns complex medical reports into plain-language explanations, helping you prepare for more informed conversations with your care team.
        </p>
        <a className="hero-cta" href="#simplify">
          Simplify a report <span aria-hidden="true">↓</span>
        </a>
      </motion.div>
      <a className="scroll-cue" href="#how-it-works" aria-label="Learn how ClearMed works">
        <span>How it works</span><i aria-hidden="true" />
      </a>
    </section>
  );
}
