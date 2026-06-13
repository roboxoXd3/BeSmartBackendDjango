import os
import threading
import boto3
from django.conf import settings

# R2 configuration defaults
R2_ACCOUNT_ID = getattr(settings, 'R2_ACCOUNT_ID', "2c1e120f3a8839f822bbbd14872467aa")
R2_ACCESS_KEY_ID = getattr(settings, 'R2_ACCESS_KEY_ID', "271011baec0bfdca8bb7bbff27620df0")
R2_SECRET_ACCESS_KEY = getattr(settings, 'R2_SECRET_ACCESS_KEY', "2937ef5bf8ef2e652779fa315cae118176cc03d69508526c6783809b369bc9f3")
R2_BUCKET_NAME = getattr(settings, 'R2_BUCKET_NAME', "my-assets")
R2_PUBLIC_URL = getattr(settings, 'R2_PUBLIC_URL', "https://pub-6b2eeaf8a8b847a8aa87b881a1033ee2.r2.dev")

def get_r2_client():
    return boto3.client(
        's3',
        endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )

def get_r2_public_url(key):
    return f"{R2_PUBLIC_URL}/{key}"

def upload_file_to_r2(file_obj, key, content_type=None):
    """Sync upload a file object to R2 and return the public URL"""
    client = get_r2_client()
    extra_args = {}
    if content_type:
        extra_args['ContentType'] = content_type
    
    client.upload_fileobj(
        file_obj,
        R2_BUCKET_NAME,
        key,
        ExtraArgs=extra_args
    )
    return get_r2_public_url(key)

def _async_upload_worker(job_id, file_path, r2_key, content_type, product_id):
    from products.models import MediaUploadJob, Product
    try:
        client = get_r2_client()
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
            
        with open(file_path, 'rb') as f:
            client.upload_fileobj(
                f,
                R2_BUCKET_NAME,
                r2_key,
                ExtraArgs=extra_args
            )
            
        public_url = get_r2_public_url(r2_key)
        
        # Update Job
        job = MediaUploadJob.objects.get(id=job_id)
        job.status = 'completed'
        job.result_url = public_url
        job.save(update_fields=['status', 'result_url'])
        
        # Update Product
        if product_id:
            Product.objects.filter(id=product_id).update(video_url=public_url)
            
    except Exception as e:
        try:
            job = MediaUploadJob.objects.get(id=job_id)
            job.status = 'failed'
            job.error_message = str(e)
            job.save(update_fields=['status', 'error_message'])
        except Exception:
            pass
    finally:
        # Cleanup temp file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

def start_async_upload(job_id, file_path, r2_key, content_type, product_id):
    """Start an async upload to R2 using a background thread."""
    thread = threading.Thread(
        target=_async_upload_worker,
        args=(job_id, file_path, r2_key, content_type, product_id)
    )
    thread.daemon = True
    thread.start()
