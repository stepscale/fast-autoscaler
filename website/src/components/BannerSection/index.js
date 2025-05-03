import React from 'react';
import Link from '@docusaurus/Link';
import styles from './styles.module.css';

export default function BannerSection() {
    return (
        <div className={styles.bannerContainer}>
            {/* The image is used as a background via CSS */}
            <div className={styles.bannerContent}>
                <h1 className={styles.title}>Fast Autoscaler</h1>
                <p className={styles.subtitle}>Intelligent ECS scaling based on queue metrics</p>

                {/* This is the actual clickable button */}
                <div className={styles.buttonContainer}>
                    <Link
                        className={styles.button}
                        to="/docs/fast-autoscaler/intro">
                        Get Started →
                    </Link>
                </div>
            </div>
        </div>
    );
}