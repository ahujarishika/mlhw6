import torch
import torch.nn as nn
import torchvision.transforms as transforms
import torch.optim as optim
import torchvision.datasets as datasets
import imageio
import numpy as np
from torchvision.utils import make_grid, save_image
from torch.utils.data import DataLoader
from matplotlib import pyplot as plt
from tqdm import tqdm


# learning parameters
batch_size = 512
epochs = 100
sample_size = 64 # fixed sample size for generator
nz = 128 # latent vector size
k = 1 # number of steps to apply to the discriminator
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


# PREPARE DATA
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.5,),(0.5,)),
])
to_pil_image = transforms.ToPILImage()

# Load train data
train_data = datasets.MNIST(
    root='homework6/data/input',
    train=True,
    download=True,
    transform=transform
)
train_loader = DataLoader(train_data, batch_size=batch_size, shuffle=True)



# MODEL CLASSES
# Generator
class Generator(nn.Module):

    def __init__(self, nz):
        super(Generator, self).__init__()
        self.nz = nz
        self.main = nn.Sequential(
            nn.Linear(self.nz, 256),
            nn.LeakyReLU(0.2),
            nn.Linear(256, 512),
            nn.LeakyReLU(0.2),
            nn.Linear(512, 1024),
            nn.LeakyReLU(0.2),
            nn.Linear(1024, 784),
            nn.Tanh(),
        )

    def forward(self, x):
        return self.main(x).view(-1, 1, 28, 28)
    
# Discriminator
class Discriminator(nn.Module):

    def __init__(self):
        super(Discriminator, self).__init__()
        self.n_input = 784
        self.main = nn.Sequential(
            nn.Linear(self.n_input, 1024),
            nn.LeakyReLU(0.2),
            nn.Dropout(0.3),
            nn.Linear(1024, 512),
            nn.LeakyReLU(0.2),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.LeakyReLU(0.2),
            nn.Dropout(0.3),
            nn.Linear(256, 1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        x = x.view(-1, 784)
        return self.main(x)

generator = Generator(nz).to(device)
discriminator = Discriminator().to(device)
# print('##### GENERATOR #####')
# print(generator)
# print('######################')
# print('\n##### DISCRIMINATOR #####')
# print(discriminator)
# print('######################')



# TRAINING TOOLS
# optimizers
optim_g = optim.Adam(generator.parameters(), lr=0.0002)
optim_d = optim.Adam(discriminator.parameters(), lr=0.0002)

# loss function
criterion = nn.BCELoss() # Binary Cross Entropy loss
losses_g = [] # to store generator loss after each epoch
losses_d = [] # to store discriminator loss after each epoch
images = [] # to store images generatd by the generator

# to create real labels (1s)
def label_real(size):
    data = torch.ones(size, 1)
    return data.to(device)

# to create fake labels (0s)
def label_fake(size):
    data = torch.zeros(size, 1)
    return data.to(device)

# function to create the noise vector
def create_noise(sample_size, nz):
    return torch.randn(sample_size, nz).to(device)

# to save the images generated by the generator
def save_generator_image(image, path):
    save_image(image, path)

# create the noise vector - fixed to track how GAN is trained.
noise = create_noise(sample_size, nz)

# # Training Loop
torch.manual_seed(7777)

def generator_loss(output, true_label):
    return criterion(output, true_label)
    
def discriminator_loss(output, true_label):
    return criterion(output, true_label)

for epoch in range(epochs):
    loss_g = 0.0
    loss_d = 0.0
    for bi, data in tqdm(enumerate(train_loader), total=int(len(train_data)/train_loader.batch_size)):

        x = data[0]

        ### UPDATE DISCRIMINATOR ###
        optim_d.zero_grad() # initialize gradient

        # real pass
        real_output = discriminator.forward(x)
        d_loss_real = discriminator_loss(real_output, label_real(real_output.size()[0]))

        # fake pass
        fake_data = generator.forward(create_noise(sample_size, nz))
        fake_output = discriminator.forward(fake_data)
        d_loss_fake = discriminator_loss(fake_output, label_fake(sample_size))

        loss_D = d_loss_real + d_loss_fake
        loss_D.backward()
        optim_d.step()

        loss_d += loss_D.detach().numpy()

        ### UPDATE GENERATOR ###
        optim_g.zero_grad() # initialize gradient

        generated_data = generator.forward(create_noise(sample_size, nz))
        generated_output = discriminator.forward(generated_data)
        loss_G = generator_loss(generated_output, label_real(sample_size)) # we want to trick the discriminator on this pass

        loss_G.backward()
        optim_g.step()

        loss_g += loss_G.detach().numpy()
        ######################################
    
    
    # create the final fake image for the epoch
    generated_img = generator(noise).cpu().detach()
    
    # make the images as grid
    generated_img = make_grid(generated_img)
    
    # visualize generated images
    if (epoch + 1) % 5 == 0:
        plt.imshow(generated_img.permute(1, 2, 0))
        plt.title(f'epoch {epoch+1}')
        plt.axis('off')
        # plt.show()
    
    # save the generated torch tensor models to disk
    save_generator_image(generated_img, f"homework6/data/output/gen_img{epoch+1}.png")
    images.append(generated_img)
    epoch_loss_g = loss_g / bi # total generator loss for the epoch
    epoch_loss_d = loss_d / bi # total discriminator loss for the epoch
    losses_g.append(epoch_loss_g)
    losses_d.append(epoch_loss_d)
    
    print(f"Epoch {epoch+1} of {epochs}")
    print(f"Generator loss: {epoch_loss_g:.8f}, Discriminator loss: {epoch_loss_d:.8f}")

print('DONE TRAINING')
torch.save(generator.state_dict(), 'homework6/data/output/generator.pth')

# save the generated images as GIF file
imgs = [np.array(to_pil_image(img)) for img in images]
imageio.mimsave('homework6/data/output/generator_images.gif', imgs)

# plot and save the generator and discriminator loss
plt.figure()
plt.plot(losses_g, label='Generator loss')
plt.plot(losses_d, label='Discriminator Loss')
plt.legend()
plt.savefig('homework6/data/output/loss.png')


if __name__ == '__main__':
    pass
