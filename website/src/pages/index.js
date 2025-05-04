import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import HomepageFeatures from '@site/src/components/HomepageFeatures';

import styles from './index.module.css';

function HomepageHeader() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <header className={styles.heroBanner}>
      <div className={styles.heroOverlay}></div>
      <div className={styles.heroGrid}>
        <div className={styles.heroContent}>
          <h1 className={styles.heroTitle}>{siteConfig.title}</h1>
          <p className={styles.heroSubtitle}>{siteConfig.tagline}</p>
          <div className={styles.heroButtons}>
            <Link
              className="button button--primary button--lg"
              to="/docs/fast-autoscaler/intro">
              Explore Fast Autoscaler
            </Link>
            <Link
              className={clsx("button button--outline", styles.secondaryButton)}
              to="/docs/intro">
              Learn More
            </Link>
          </div>
        </div>
        <div className={styles.heroImageContainer}>
          <div className={styles.autoScalingAnimation}>
            <div className={styles.queueContainer}>
              <div className={styles.queueTitle}>SQS Queue</div>
              <div className={styles.queueBar}>
                <div className={styles.queueFill}></div>
              </div>
              <div className={styles.messageIndicators}>
                <div className={styles.messageIcon}></div>
                <div className={styles.messageIcon}></div>
                <div className={styles.messageIcon}></div>
                <div className={styles.messageIcon}></div>
                <div className={styles.messageIcon}></div>
                <div className={styles.messageIcon}></div>
                <div className={styles.messageIcon}></div>
                <div className={styles.messageIcon}></div>
              </div>
            </div>

            <div className={styles.autoscalerContainer}>
              <div className={styles.autoscalerTitle}>Fast Autoscaler</div>
              <div className={styles.autoscalerIcon}>
                <div className={styles.gearOne}></div>
                <div className={styles.gearTwo}></div>
              </div>
            </div>

            <div className={styles.tasksContainer}>
              <div className={styles.tasksTitle}>ECS Tasks</div>
              <div className={styles.tasksGrid}>
                <div className={styles.taskBlock}></div>
                <div className={styles.taskBlock}></div>
                <div className={styles.taskBlock}></div>
                <div className={styles.taskBlock}></div>
                <div className={styles.taskBlock}></div>
                <div className={styles.taskBlock}></div>
                <div className={styles.taskBlock + ' ' + styles.taskScaleIn}></div>
                <div className={styles.taskBlock + ' ' + styles.taskScaleIn}></div>
                <div className={styles.taskBlock + ' ' + styles.taskScaleIn}></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

function ModernFooter() {
  const { siteConfig } = useDocusaurusContext();

  return (
    <footer className={styles.modernFooter}>
      <div className={styles.footerOverlay}></div>

      <div className="container">
        <div className={styles.footerGrid}>
          {/* Company Info Column */}
          <div className={styles.footerCol}>
            <div className={styles.footerLogo}>
              {/* Use existing company logo instead of animated icon */}
              <img
                src="/img/stepscale-logo.png"
                alt="StepScale.io Logo"
                className={styles.logoImage}
              />
              <span>{siteConfig.title}</span>
            </div>
            <p className={styles.footerTagline}>
              Cloud-native scaling solutions that evolve with your business
            </p>
            <div className={styles.socialLinks}>
              <a href="https://github.com/stepscale" className={styles.socialIcon}>
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path>
                </svg>
              </a>
              <a href="https://twitter.com/stepscaleio" className={styles.socialIcon}>
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 4s-.7 2.1-2 3.4c1.6 10-9.4 17.3-18 11.6 2.2.1 4.4-.6 6-2C3 15.5.5 9.6 3 5c2.2 2.6 5.6 4.1 9 4-.9-4.2 4-6.6 7-3.8 1.1 0 3-1.2 3-1.2z"></path>
                </svg>
              </a>
              <a href="https://www.linkedin.com/company/stepscale" className={styles.socialIcon}>
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path>
                  <rect x="2" y="9" width="4" height="12"></rect>
                  <circle cx="4" cy="4" r="2"></circle>
                </svg>
              </a>
            </div>
          </div>

          {/* Products Column */}
          <div className={styles.footerCol}>
            <h3 className={styles.footerHeading}>Products</h3>
            <ul className={styles.footerLinks}>
              <li>
                <Link to="/docs/fast-autoscaler/intro">Fast Autoscaler</Link>
              </li>
              {/* <li>
                <Link to="/docs/roadmap">Product Roadmap</Link>
              </li>
              <li>
                <Link to="/docs/fast-autoscaler/changelog">Changelog</Link>
              </li> */}
            </ul>
          </div>

          {/* Resources Column */}
          <div className={styles.footerCol}>
            <h3 className={styles.footerHeading}>Resources</h3>
            <ul className={styles.footerLinks}>
              <li>
                <Link to="/docs/fast-autoscaler/intro">Documentation</Link>
              </li>
              <li>
                <Link to="https://github.com/stepscale/fast-autoscaler">GitHub</Link>
              </li>
              <li>
                <Link to="/docs/articles/intro">Tutorials & Articles</Link>
              </li>
            </ul>
          </div>

          {/* Company Column */}
          <div className={styles.footerCol}>
            <h3 className={styles.footerHeading}>Company</h3>
            <ul className={styles.footerLinks}>
              <li>
                <Link to="/docs/about-us">About Us</Link>
              </li>
              <li>
                <Link to="/docs/contact">Contact</Link>
              </li>
              <li>
                <Link to="/legal/privacy">Privacy Policy</Link>
              </li>
            </ul>
          </div>

          {/* Newsletter Column */}
          <div className={clsx(styles.footerCol, styles.footerNewsletter)}>
            <h3 className={styles.footerHeading}>Stay Updated</h3>
            <p>Subscribe to our newsletter for the latest updates and releases.</p>
            <form className={styles.subscribeForm}>
              <input
                type="email"
                placeholder="Your email address"
                className={styles.subscribeInput}
              />
              <button className={styles.subscribeButton}>Subscribe</button>
            </form>
          </div>
        </div>

        <div className={styles.footerBottom}>
          <div className={styles.copyright}>
            © {new Date().getFullYear()} StepScale.io. All rights reserved.
          </div>
          <div className={styles.footerBottomLinks}>
            <Link to="/legal/terms">Terms</Link>
            <Link to="/legal/privacy">Privacy</Link>
            <Link to="/docs/contact">Support</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default function Home() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <Layout
      title={`${siteConfig.title} - Cloud-native scaling solutions`}
      description="StepScale.io provides cloud-native scaling solutions that evolve with your business. Our first product, Fast Autoscaler, optimizes AWS ECS services based on SQS queue metrics.">
      <HomepageHeader />
      <main>
        <section className={styles.section}>
          <div className="container">
            <div className="row">
              <div className="col col--8 col--offset-2">
                <h2 className={styles.sectionTitle}>About StepScale.io</h2>
                <p>
                  StepScale.io specializes in building intelligent scaling solutions for modern cloud infrastructure.
                  We help companies optimize their cloud resources, reduce operational costs, and improve system reliability
                  through advanced autoscaling technologies.
                </p>
                <p>
                  Our team brings together expertise in cloud infrastructure, serverless architectures, and software
                  engineering to create tools that simplify complex scaling challenges.
                </p>
              </div>
            </div>
          </div>
        </section>

        <HomepageFeatures />

        <section className={clsx(styles.section, styles.sectionAlt)}>
          <div className="container">
            <div className="row">
              <div className="col col--8 col--offset-2">
                <h2 className={styles.sectionTitle}>Our Products</h2>
                <div className={styles.productCard}>
                  <h3>Fast Autoscaler</h3>
                  <p>
                    A modular, extensible autoscaling solution for AWS ECS services based on queue metrics.
                    Fast Autoscaler dynamically adjusts your service's task count based on SQS queue depths
                    to optimize both performance and cost.
                  </p>
                  <div className={styles.buttonContainer}>
                    <Link
                      className={clsx("button button--primary", styles.productButton)}
                      to="/docs/fast-autoscaler/intro">
                      Learn More
                    </Link>
                    <Link
                      className={clsx("button button--secondary", styles.productButton)}
                      to="https://github.com/stepscale/fast-autoscaler">
                      View on GitHub
                    </Link>
                  </div>
                </div>
                {/* Additional product cards can be added here as the company grows */}
              </div>
            </div>
          </div>
        </section>

        <section className={styles.section}>
          <div className="container">
            <div className="row">
              <div className="col col--8 col--offset-2 text--center">
                <h2 className={styles.sectionTitle}>Get Started Today</h2>
                <p>
                  Ready to optimize your cloud resources? Explore our documentation or contribute to our open source projects.
                </p>
                <div className={styles.buttonContainer}>
                  <Link className="button button--primary button--lg" to="/docs/intro">
                    Documentation
                  </Link>
                  <Link className="button button--secondary button--lg" to="/docs/contact">
                    Contact Us
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
      <ModernFooter />
    </Layout>
  );
}
