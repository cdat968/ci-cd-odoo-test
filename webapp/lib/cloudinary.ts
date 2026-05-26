import { v2 as cloudinary } from 'cloudinary';

// cloudinary auto-configures from CLOUDINARY_URL env var
// https://cloudinary.com/documentation/node_integration#setting_configuration_parameters_globally

export async function uploadImage(
  filePath: string,
  folder?: string,
): Promise<{ secure_url: string; public_id: string }> {
  const result = await cloudinary.uploader.upload(filePath, {
    folder,
    resource_type: 'image',
  });
  return { secure_url: result.secure_url, public_id: result.public_id };
}

export async function deleteImage(publicId: string): Promise<void> {
  await cloudinary.uploader.destroy(publicId);
}
