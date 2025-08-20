# SEC Filings QA Agent - Render Deployment Guide

## 🚀 Quick Deploy to Render

### Prerequisites
1. GitHub account with your code repository
2. Render account (free tier available)
3. SEC API key from sec-api.io
4. Google Gemini API key

### Step 1: Prepare Your Repository

1. **Ensure all files are committed to your GitHub repository:**
   ```bash
   git add .
   git commit -m "Ready for Render deployment"
   git push origin main
   ```

2. **Verify these files exist in your repository:**
   - `Dockerfile.render` (production Dockerfile)
   - `requirements.txt` (with pinned versions)
   - `app.py` (main application file)
   - All source code and frontend files

### Step 2: Deploy on Render

1. **Go to [Render Dashboard](https://dashboard.render.com/)**

2. **Click "New +" → "Web Service"**

3. **Connect your GitHub repository:**
   - Select your GitHub account
   - Choose the SEC_Filings_QA_Agent repository
   - Click "Connect"

4. **Configure the web service:**
   ```
   Name: sec-filings-qa-agent
   Environment: Docker
   Region: Oregon (US West) - or closest to you
   Branch: main
   Dockerfile Path: Dockerfile.render
   ```

5. **Set environment variables:**
   ```
   SEC_API_KEY=your_sec_api_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-2.0-flash
   FLASK_ENV=production
   FLASK_DEBUG=False
   DATABASE_PATH=data/sec_filings.db
   VECTOR_DB_PATH=data/vector_index
   EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
   CHUNK_SIZE=1000
   CHUNK_OVERLAP=200
   LOG_LEVEL=INFO
   LOG_FILE=logs/app.log
   ```

6. **Choose plan:**
   - **Free Tier**: Good for testing (spins down after 15 min of inactivity)
   - **Starter ($7/month)**: Recommended for production (always on)

7. **Click "Create Web Service"**

### Step 3: Monitor Deployment

1. **Watch the build logs:**
   - Render will pull your code
   - Build the Docker image
   - Deploy the container

2. **Build typically takes 5-10 minutes**

3. **Once deployed, you'll get a URL like:**
   ```
   https://sec-filings-qa-agent.onrender.com
   ```

### Step 4: Test Your Deployment

1. **Open your Render URL**
2. **Test the health check:**
   ```
   https://your-app.onrender.com/api/v1/health
   ```
3. **Try the web interface**
4. **Submit a test question**

### Step 5: Set Up Persistent Storage (Optional)

For persistent data across deployments:

1. **Go to Render Dashboard → Disks**
2. **Create a new disk:**
   ```
   Name: sec-filings-data
   Size: 1GB (free tier)
   ```
3. **Mount to your web service:**
   ```
   Mount Path: /app/data
   ```

### Troubleshooting

#### Build Failures
```bash
# Check Dockerfile.render syntax
# Verify requirements.txt format
# Ensure all dependencies are available
```

#### Runtime Errors
```bash
# Check environment variables are set
# Verify API keys are valid
# Check logs in Render dashboard
```

#### Performance Issues
```bash
# Upgrade to Starter plan for better performance
# Add more resources if needed
# Monitor memory usage
```

### Environment Variables Reference

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `SEC_API_KEY` | ✅ | SEC API key from sec-api.io | - |
| `GEMINI_API_KEY` | ✅ | Google Gemini API key | - |
| `GEMINI_MODEL` | ❌ | Gemini model name | gemini-2.0-flash |
| `FLASK_ENV` | ❌ | Flask environment | production |
| `FLASK_DEBUG` | ❌ | Debug mode | False |
| `DATABASE_PATH` | ❌ | SQLite database path | data/sec_filings.db |
| `VECTOR_DB_PATH` | ❌ | Vector index path | data/vector_index |
| `EMBEDDING_MODEL` | ❌ | Sentence transformer model | sentence-transformers/all-MiniLM-L6-v2 |
| `CHUNK_SIZE` | ❌ | Document chunk size | 1000 |
| `CHUNK_OVERLAP` | ❌ | Chunk overlap size | 200 |
| `LOG_LEVEL` | ❌ | Logging level | INFO |

### Custom Domain (Optional)

1. **Go to Settings → Custom Domains**
2. **Add your domain**
3. **Configure DNS records as shown**
4. **Wait for SSL certificate provisioning**

### Scaling and Performance

#### Free Tier Limitations
- Spins down after 15 minutes of inactivity
- Cold start delay (~30 seconds)
- Limited CPU and memory

#### Upgrade Recommendations
- **Starter Plan**: Always-on, better performance
- **Pro Plan**: More resources, faster response times

### Monitoring and Logs

1. **View logs in Render dashboard**
2. **Set up health checks:**
   ```
   Health Check Path: /api/v1/health
   ```
3. **Monitor performance metrics**

### Backup Strategy

1. **Regular database exports**
2. **Vector index backups**
3. **Configuration backups**
4. **Code repository as primary backup**

### Security Best Practices

1. **Never commit API keys to repository**
2. **Use environment variables for secrets**
3. **Enable HTTPS (automatic on Render)**
4. **Regular dependency updates**
5. **Monitor for security vulnerabilities**

### Cost Optimization

1. **Start with free tier for testing**
2. **Upgrade only when needed**
3. **Monitor usage patterns**
4. **Use efficient resource allocation**

---

## 🎉 Congratulations!

Your SEC Filings QA Agent is now deployed on Render and accessible worldwide!

**Next steps:**
1. Test all functionality
2. Process some SEC filings
3. Ask questions and verify answers
4. Monitor performance and costs
5. Set up monitoring and alerts

**Support:**
- [Render Documentation](https://render.com/docs)
- [Render Community](https://community.render.com/)
- Check application logs for debugging
